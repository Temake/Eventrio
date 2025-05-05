from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
import requests
from .permissions import IsEventCreator
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import os
from .utils import send_whatsapp_message
from django.shortcuts import get_object_or_404

from .models import Event, Attendee, Reminder
from .serializers import (
    UserSerializer,
    EventSerializer,
    EventDetailSerializer,
    AttendeeSerializer,
    ReminderSerializer,
    UserProfileSerializer,
    SocialAccountSeralizer,
)


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Generate a token for the user
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "user": UserSerializer(
                        user, context=self.get_serializer_context()
                    ).data,
                    "message": "User registered successfully",
                    "token": token.key,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsEventCreator]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        user = self.request.user
        return Event.objects.filter(creator=user)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return EventDetailSerializer
        return EventSerializer

    @action(detail=True, methods=["get"])
    def attendees(self, request, pk=None):
        event = self.get_object()
        attendees = event.attendees.all()
        serializer = AttendeeSerializer(attendees, many=True)
        return Response(serializer.data)


class PublicEventListView(generics.ListAPIView):
    serializer_class = EventSerializer
    queryset = Event.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class AttendeeView(generics.ListAPIView):
    serializer_class = AttendeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        user = self.request.user
        event_id = self.kwargs.get("id")
        return Attendee.objects.filter(event__id=event_id, event__creator=user)


class EventRegistrationView(generics.GenericAPIView):
    serializer_class = AttendeeSerializer
    permission_classes = [permissions.AllowAny]

    def get(self, request, registration_link=None):

        # Find the event by matching the registration code in the registration_link
        event = get_object_or_404(Event, registration_link=registration_link)
        return Response({"event": EventSerializer(event).data})

    def post(self, request, registration_link=None):

        event = get_object_or_404(Event, registration_link=registration_link)
        whatsapp_number = request.data.get("phone_number")
        attendee = request.data.get("email")
        serializer = self.get_serializer(
            data=request.data, context={"event_id": event.id}
        )

        if serializer.is_valid():
            serializer.save()

            context = {
                "event_title": event.title,
                "event_date": event.date,
                "event_time": event.time,
                "event_location": event.location,
                "attendee_email": attendee,
            }
            html_message = render_to_string("emails/event_registration.html", context)
            plain_message = strip_tags(html_message)

            try:
                send_mail(
                    subject=f"You have Successfully registered for {event.title}",
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[attendee],
                    fail_silently=False,
                    html_message=html_message,
                )

                # # Create a reminder record
                # Reminder.objects.create(
                #     attendee=attendee,
                #     message=message,
                #     type='EMAIL'
                # )

            except Exception as e:
                print(f"Failed to send email reminder: {str(e)}")
            # try:
            #     send_whatsapp_message(whatsapp_number, message)
            # except Exception as e:
            #     print(f"Failed to send Whatsapp Message: {str(e)}")

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def logout(request):
    try:
        request.user.auth_token.delete()
        return Response(
            {"message": "Logged out successfully."}, status=status.HTTP_200_OK
        )
    except (AttributeError, Token.DoesNotExist):
        return Response(
            {"message": "User is not logged in."}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET"])
def google(request):
    code = request.GET.get("code")
    if code is None:
        return Response({"message": "No code provided"}, status=400)

    PARAMS = {
        "client_id": os.environ.get("google_id") or "",
        "client_secret": os.environ.get("google_secret"),
        "redirect_uri": os.environ.get("redirect_url"),
        "code": code,
        "grant_type": "authorization_code",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_response = requests.post(
        "https://oauth2.googleapis.com/token", data=PARAMS, headers=headers
    )

    if token_response.status_code != 200:
        return Response(
            {"message": "Failed to get access token", "error": token_response.json()},
            status=400,
        )

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    user_info_response = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if user_info_response.status_code != 200:
        return Response({"message": "Failed to fetch user info"}, status=400)

    user_info = user_info_response.json()
    existing_user = User.objects.filter(email=user_info["email"]).first()

    if existing_user:
        token, created = Token.objects.get_or_create(user=existing_user)
        user_data = UserSerializer(existing_user).data
        return Response({"user": user_data, "token": token.key}, status=200)

    # Creating a new user
    create_user = SocialAccountSeralizer(
        data={
            "email": user_info["email"],
            "username": user_info["given_name"],
            "phone_number": user_info["phone_number"],
        }
    )

    if create_user.is_valid():
        user_instance = create_user.save()
        token, created = Token.objects.get_or_create(user=user_instance)

        return Response({"user": create_user.data, "token": token.key}, status=200)

    return Response(
        {"message": "An error occured, Please try again later"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
