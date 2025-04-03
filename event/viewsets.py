from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Event, Attendee, Reminder
from .serializers import (
    UserSerializer, EventSerializer, EventDetailSerializer, 
    AttendeeSerializer, ReminderSerializer
)

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "user": UserSerializer(user, context=self.get_serializer_context()).data,
                "message": "User registered successfully",
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