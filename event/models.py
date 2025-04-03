from django.db import models
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.utils import timezone
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20)
    confirm_password=models.CharField(max_length=154,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    registration_link = models.CharField(max_length=255, unique=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.registration_link:
            self.registration_link = f"{self.id}-{get_random_string(8)}"
        super().save(*args, **kwargs)
    
    @property
    def creator_phone_number(self):
        return self.creator.profile.phone_number
    
    def __str__(self):
        return self.title
class Attendee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendees')
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    registered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('event', 'email')
    
    def __str__(self):
        return f"{self.name} - {self.event.title}"

class Reminder(models.Model):
    attendee = models.ForeignKey(Attendee, on_delete=models.CASCADE, related_name='reminders')
    sent_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=[('EMAIL', 'Email'), ('WHATSAPP', 'WhatsApp')])
    
    def __str__(self):
        return f"Reminder to {self.attendee.name} via {self.type}"