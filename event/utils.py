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


import requests
import json
import logging
from django.conf import settings

# Set up logging
logger = logging.getLogger(__name__)

def send_whatsapp_message(to, message, message_type='text'):
    """
    Send a WhatsApp message using the WhatsApp Business API
    
    Args:
        to (str): The recipient's phone number in international format (without +)
        message (str): The message content to send
        message_type (str): The type of message ('text', 'template', etc.)
    
    Returns:
        dict: The API response
    """
    try:
        # Ensure the phone number is in the correct format
        if to.startswith('+'):
            to = to[1:]  # Remove the + if present
            
        api_url = settings.WHATSAPP_API_URL
        headers = {
            'Authorization': f'Bearer {settings.WHATSAPP_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Build the payload based on message type
        if message_type == 'text':
            payload = {
                'messaging_product': 'whatsapp',
                'recipient_type': 'individual',
                'to': to,
                'type': 'text',
                'text': {'body': message}
            }
        elif message_type == 'template':
            # You would need to customize this for your specific templates
            payload = {
                'messaging_product': 'whatsapp',
                'recipient_type': 'individual',
                'to': to,
                'type': 'template',
                'template': {
                    'name': message['template_name'],
                    'language': {'code': 'en_US'},
                    'components': message['components']
                }
            }
        else:
            raise ValueError(f"Unsupported message type: {message_type}")
        
        # Send the request
        response = requests.post(api_url, json=payload, headers=headers)
        response_data = response.json()
        
        # Log the response
        if response.status_code != 200:
            logger.error(f"WhatsApp API error: {response.status_code} - {response_data}")
        else:
            logger.info(f"WhatsApp message sent to {to}")
            
        return response_data
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
    