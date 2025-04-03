import os
from .utils import send_whatsapp_message
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from celery import shared_task
from .models import Event,  Reminder

@shared_task
def send_event_reminders():
  
    # Find events that are coming up in the next 24 hours or 4days
    tomorrow = timezone.now() + timedelta(days=1)
    four_days = timezone.now() + timedelta(days=4)
    
    # Get events in the next 3 days
    upcoming_events = Event.objects.filter(
        date__gte=tomorrow,
        date__lte=four_days
    )
    
    for event in upcoming_events:
        days_until_event = (event.date - timezone.now()).days
        
        for attendee in event.attendees.all():
         
            if Reminder.objects.filter(
                attendee=attendee,
                sent_at__date=timezone.now().date()
            ).exists():
                continue
            
            
            if days_until_event <= 1:
                message = f"REMINDER: The event '{event.title}' is TOMORROW at {event.date.strftime('%H:%M')} in {event.location}."
            else:
                message = f"REMINDER: The event '{event.title}' is coming up in {days_until_event} days at {event.date.strftime('%H:%M')} in {event.location}."
            
            # Send email reminder
            send_email_reminder(attendee, event, message)
            
            # Send WhatsApp reminder if phone number is available
            if attendee.phone_number:
                send_whatsapp_reminder(attendee, message)

def send_email_reminder(attendee, event, message):
    """Send email reminder to an attendee"""
    try:
        send_mail(
            subject=f"Reminder: {event.title}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[attendee.email],
            fail_silently=False,
        )
        
        # Record the reminder
        Reminder.objects.create(
            attendee=attendee,
            message=message,
            type='EMAIL'
        )
        
    except Exception as e:
        print(f"Failed to send email reminder: {str(e)}")

def send_whatsapp_reminder(attendee, message):
    """Send WhatsApp reminder to an attendee"""
    try:
      
        send_whatsapp_message(attendee.phone_number, message)
        
        
        Reminder.objects.create(
            attendee=attendee,
            message=message,
            type='WHATSAPP'
        )
        
    except Exception as e:
        print(f"Failed to send WhatsApp reminder: {str(e)}")