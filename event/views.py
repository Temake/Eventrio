from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.permissions import AllowAny
from django.http import HttpResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
import requests
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
import os
from .utils import send_whatsapp_message
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.openapi import OpenApiTypes

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
from django.views.decorators.csrf import csrf_exempt
import json
import hmac
import hashlib


@extend_schema(
    summary="WhatsApp Webhook",
    description="Webhook endpoint for WhatsApp Business API integration with AI-powered responses",
    methods=['GET', 'POST'],
    responses={
        200: {'description': 'Webhook processed successfully'},
        403: {'description': 'Invalid verification token'},
        500: {'description': 'Error processing webhook'}
    },
    tags=['WhatsApp Integration']
)
@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def whatsapp_webhook(request):
    """
    WhatsApp Webhook endpoint - handles both verification and incoming messages
    """
    if request.method == 'GET':
        # This is a verification request from WhatsApp/Meta
        mode = request.query_params.get('hub.mode')
        token = request.query_params.get('hub.verify_token')
        challenge = request.query_params.get('hub.challenge')
        
        # Verify against your configured token
        if mode == 'subscribe' and token == settings.WHATSAPP_VERIFY_TOKEN:
            return HttpResponse(challenge, status=200)
        else:
            return HttpResponse('Verification failed', status=403)
    
    elif request.method == 'POST':
        # This is an actual webhook event (incoming message etc.)
        
        # Verify the request is from WhatsApp/Meta using their signature
        signature = request.headers.get('X-Hub-Signature-256', '')
        
        if settings.WHATSAPP_APP_SECRET:
            # Get the raw body
            raw_body = request.body
            
            # Compute the expected signature
            expected_signature = 'sha256=' + hmac.new(
                settings.WHATSAPP_APP_SECRET.encode('utf-8'),
                raw_body,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures - if they don't match, reject the request
            if not hmac.compare_digest(signature, expected_signature):
                return HttpResponse('Invalid signature', status=403)
        
        # Process the webhook data
        try:
            data = json.loads(request.body)
            
            # Check if this is a WhatsApp message
            if 'object' in data and data['object'] == 'whatsapp_business_account':
                # Process each entry
                for entry in data.get('entry', []):
                    for change in entry.get('changes', []):
                        value = change.get('value', {})
                        
                        # Process messages
                        if 'messages' in value:
                            for message in value['messages']:
                                # Extract relevant information
                                phone_number = message.get('from', '')
                                message_body = message.get('text', {}).get('body', '')
                                message_id = message.get('id', '')
                                
                                # Process the message (using your existing logic)
                                send_whatsapp_message(phone_number, message_body)
                
                return HttpResponse('Webhook received successfully', status=200)
            
            return HttpResponse('Ignored', status=200)
            
        except Exception as e:
            return HttpResponse(f'Error processing webhook: {str(e)}', status=500)
    
    return HttpResponse('Method not allowed', status=405)


@extend_schema(
    summary="User Registration",
    description="Register a new user with email, password, and phone number",
    request=UserSerializer,
    responses={
        201: {
            'description': 'User created successfully',
            'examples': {
                'application/json': {
                    'user': {'id': 1, 'username': 'john@example.com', 'email': 'john@example.com'},
                    'message': 'User registered successfully',
                    'token': 'your-auth-token-here'
                }
            }
        },
        400: {'description': 'Validation errors'}
    },
    tags=['Authentication']
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


@extend_schema(
    summary="Event Management",
    description="CRUD operations for events. Users can create, list, update, and delete their own events.",
    tags=['Events']
)
class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
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

    @extend_schema(
        summary="Get Event Attendees",
        description="Retrieve all attendees for a specific event",
        responses={200: AttendeeSerializer(many=True)},
        tags=['Events']
    )
    @action(detail=True, methods=["get"])
    def attendees(self, request, pk=None):
        event = self.get_object()
        attendees = event.attendees.all()
        serializer = AttendeeSerializer(attendees, many=True)
        return Response(serializer.data)


@extend_schema(
    summary="Public Events List",
    description="Get a list of all public events without authentication",
    responses={200: EventSerializer(many=True)},
    tags=['Public']
)
class PublicEventListView(generics.ListAPIView):
    serializer_class = EventSerializer
    queryset = Event.objects.all()

    permission_classes = [permissions.AllowAny]


@extend_schema(
    summary="Event Attendees",
    description="Get attendees for a specific event (creator only)",
    parameters=[
        OpenApiParameter(
            name='id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='Event ID'
        )
    ],
    responses={200: AttendeeSerializer(many=True)},
    tags=['Events']
)
class AttendeeView(generics.ListAPIView):
    serializer_class = AttendeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        user = self.request.user
        event_id = self.kwargs.get("id")
        return Attendee.objects.filter(event__id=event_id, event__creator=user)


@extend_schema(
    summary="Event Registration",
    description="Register for an event using a registration link",
    parameters=[
        OpenApiParameter(
            name='registration_link',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='Unique registration link for the event'
        )
    ],
    request=AttendeeSerializer,
    responses={
        201: {
            'description': 'Registration successful',
            'examples': {
                'application/json': {
                    'message': 'Registration successful! Confirmation sent via email and WhatsApp.'
                }
            }
        },
        400: {'description': 'Already registered or validation error'},
        404: {'description': 'Event not found'}
    },
    tags=['Registration']
)
class EventRegistrationView(generics.GenericAPIView):
    serializer_class = AttendeeSerializer
    permission_classes = [permissions.AllowAny]

    # def get(self, request):

    #     # Find the event by matching the registration code in the registration_link
    #     event = get_object_or_404(Event)
    #     return Response({
    #         'event': EventSerializer(event).data
    #     })

    def post(self, request, registration_link=None):

        event = get_object_or_404(Event, registration_link=registration_link)
        whatsapp_number = request.data.get("phone_number")
        attendee = request.data.get("email")
        serializer = self.get_serializer(
            data=request.data, context={"event_id": event.id}
        )

        if serializer.is_valid():
            serializer.save()

            # Send confirmation email
            message = f"Thank you for registering for {event.title}, We look forward to seeing you at the event"

            try:
                send_mail(
                    subject=f"You have Successfully registered for {event.title}",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[attendee],
                    fail_silently=False,
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
    token_response = requests.post("https://oauth2.googleapis.com/token", data=PARAMS, headers=headers)

    if token_response.status_code != 200:
        print(token_response.json())
        return Response({"message": "Failed to get access token", "error": token_response.json()}, status=400)

    token_data = token_response.json()
    access_token = token_data.get("access_token")

    user_info_response = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    if user_info_response.status_code != 200:
        return Response({"message": "Failed to fetch user info"}, status=400)

    user_info = user_info_response.json()
    existing_user = User.objects.filter(email=user_info["email"]).first()

    if existing_user:
        token, created = Token.objects.get_or_create(user=existing_user)
        user_data = UserSerializer(existing_user).data
        return Response({
            'user': user_data,
            'token': token.key
        }, status=200)

    # Creating a new user
    create_user =  SocialAccountSeralizer(data={"email": user_info["email"], "username": user_info["given_name"],"phone_number":user_info["phone_number"]})

    if create_user.is_valid():
        user_instance = create_user.save()
        token, created = Token.objects.get_or_create(user=user_instance)
        
        return Response({
            'user': create_user.data,
            'token': token.key
        }, status=200)

    return Response({"message":"An error occured, Pleasee try again later"},status=500)
