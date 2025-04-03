from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import requests
import google.generativeai as genai
from django.conf import settings
from .models import Event, Attendee,UserProfile

genai.configure(api_key=settings.GEMINI_API_KEY)

@api_view(['POST'])
@permission_classes([AllowAny])
def whatsapp_webhook(request):
    # Extract incoming WhatsApp message details
    data = request.data
    message = data.get('message', {})
    phone_number = data.get('from', '')
    """ PENDING FUNCTIONALITY TO SEND MESSAGE TO THE CREATOR USER WHEN PEOPLE REGISTER FOR THEIR EVENTS"""
    # try:
    #     profile = UserProfile.objects.filter(phone_number=phone_number).first()
    #     if profile:
    #         # This is an event creator
    #         # You can add specific handling for event creators here
    #         user_events = Event.objects.filter(creator=profile.user)
    #         event_list = "\n".join([f"- {event.title} on {event.date.strftime('%Y-%m-%d')}" for event in user_events])
            
    #         response_text = f"Hello {profile.user.username}! Here are your events:\n{event_list}"
    #         send_whatsapp_message(phone_number, response_text)
    #         return Response({"success": True})
    # except Exception as e:
    #     pass 
    try:
        attendee = Attendee.objects.filter(phone_number=phone_number).order_by('-registered_at').first()
        if not attendee:
            return Response({"message": "Attendee not found"}, status=400)
        
        event = attendee.event
        
        # Prepare context for Gemini from event details
        context = f"Event: {event.title}\nDescription: {event.description}\nDate: {event.date}\nLocation: {event.location}"
      
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(
            f"Context about an event: {context}\n\nUser question: {message}\n\nPlease answer based only on the event information provided."
        )
        
        # Send response back to WhatsApp
        send_whatsapp_message(phone_number, response.text)
        
        return Response({"success": True})
    
    except Exception as e:
        return Response({"error": str(e)}, status=500)

def send_whatsapp_message(to, message):
    
    api_url = settings.WHATSAPP_API_URL
    headers = {
        'Authorization': f'Bearer {settings.WHATSAPP_API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'messaging_product': 'whatsapp',
        'to': to,
        'type': 'text',
        'text': {'body': message}
    }
    
    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()