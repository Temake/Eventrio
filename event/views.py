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
# @api_view(['POST'])
# def register(request):
#     username = request.data.get('username')
#     password = request.data.get('password')
#     confirm_password=request.data.get('confirm_password')
#     email = request.data.get('email')
#     phone_number= request.data.get('phone_number')

#     if not username or not password or not email or not confirm_password or not phone_number or not email:
#         return Response({'error': 'Username,Phone Number,Email ,and password are required.'}, status=400)


#     if User.objects.filter(email=email).exists():
#         return Response({'error': 'Email is already registered.'}, status=400)
#     if User.objects.filter(username=username).exists():
#         return Response({'error': 'Username is already taken.'}, status=400)
    
#     profile= UserProfileSerializer(data={'phone_number': phone_number,'confirm_password':confirm_password})
#     user_serializer = UserSerializer(data={'username': username, 'password': password, 'email': email,'confirm_password':confirm_password,'phone_number':phone_number,'profile':profile})

#     if user_serializer.is_valid():
#         user = user_serializer.save()

#         user.set_password(password)
#         user.save()
        

#         user_profile = User(data={'user':user.id})

#         if user_profile.is_valid():
#             user_profile.save()

#         token, created = Token.objects.get_or_create(user=user)
#         return Response({
#             'user': user_serializer.data,
#             'token': token.key,
#             'profile': user_profile.data,
#         }, status=201)


#     return Response(user_serializer.errors, status=400)


# @api_view(["POST"])
# def login(request, *args, **kwargs):
#     email = request.data.get("email")
#     password = request.data.get("password")

#     if not email or not password:
#         return Response({'error': 'Email and password are required.'}, status=400)

#     try:
      
#         user = User.objects.get(email=email)
#     except User.DoesNotExist:
#         return Response({"error": "Invalid credentials."}, status=401)

#     if not user.check_password(password):
#         return Response({"error": "Invalid credentials."}, status=401)


#     user_data = UserSerializer(user).data
#     token, created = Token.objects.get_or_create(user=user)

#     return Response({
#         'user': user_data,
#         'token': token.key
#     }, status=200)



class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
        


            return Response({
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "message": "User registered successfully",
                 'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Event.objects.filter(creator=user)
    
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

class EventRegistrationView(generics.GenericAPIView):
    serializer_class = AttendeeSerializer
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, registration_link):
        event = get_object_or_404(Event, registration_link=registration_link)
        return Response({
            'event': EventSerializer(event).data
        })
    
    def post(self, request, registration_link):
        event = get_object_or_404(Event, registration_link=registration_link)
        serializer = self.get_serializer(data=request.data, context={'event_id': event.id})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def send_email_reminder(request,attendee, event, message):
   
        try:
            send_mail(
                subject=f"Your have Successfully registerd for {event.title}",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[attendee.email],
                fail_silently=False,
            )
            
            
            Reminder.objects.create(
                attendee=attendee,
                message=message,
                type='EMAIL'
            )
            
        except Exception as e:
            print(f"Failed to send email reminder: {str(e)}")
