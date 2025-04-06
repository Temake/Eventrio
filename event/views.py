from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.shortcuts import get_object_or_404

from .models import Event, Attendee, Reminder
from .serializers import (
    UserSerializer, EventSerializer, EventDetailSerializer, 
    AttendeeSerializer, ReminderSerializer,UserProfileSerializer
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
            return Response({
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "message": "User registered successfully",
                "token": token.key,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

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
        if self.action == 'retrieve':
            return EventDetailSerializer
        return EventSerializer
    
    @action(detail=True, methods=['get'])
    def attendees(self, request, pk=None):
        event = self.get_object()
        attendees = event.attendees.all()
        serializer = AttendeeSerializer(attendees, many=True)
        return Response(serializer.data)

class PublicEventListView(generics.ListAPIView):
    serializer_class = EventSerializer
    queryset = Event.objects.all()

    permission_classes = [permissions.AllowAny]

class AttendeeView(generics.ListAPIView):
    serializer_class = AttendeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]


    def get_queryset(self):
        user = self.request.user
        event_id = self.kwargs.get('id') 
        return Attendee.objects.filter(event__id=event_id, event__creator=user)

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
        attendee = request.data.get('email')
        serializer = self.get_serializer(data=request.data, context={'event_id': event.id})
        
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
                
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def logout(request):
    try:
        request.user.auth_token.delete()
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
    except (AttributeError, Token.DoesNotExist):
        return Response({"message": "User is not logged in."}, status=status.HTTP_400_BAD_REQUEST)