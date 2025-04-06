from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from .models import UserProfile, Event, Attendee, Reminder


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile details."""

    class Meta:
        model = UserProfile
        fields = ("phone_number", "confirm_password")


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user registration and profile."""

    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(write_only=True, required=True)
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "password",
            "phone_number",
            "profile",
            "confirm_password",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "confirm_password": {"write_only": True},
        }

    def validate(self, data):
        """Validate password and confirm_password fields."""
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if not password or not confirm_password:
            raise serializers.ValidationError(
                {"password": "Password and confirm password are required."}
            )
        if password != confirm_password:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return data

    def create(self, validated_data):
        """Create a new user and associate a profile."""
        email = validated_data.get("email")
        username = validated_data.get("username")
        phone_number = validated_data.pop("phone_number", None)
        validated_data.pop("confirm_password", None)

        # Check for required fields
        if not email or not username or not phone_number:
            raise serializers.ValidationError(
                {"info": "Email, username, and phone number are required."}
            )

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"info": "A user with this email already exists."}
            )

        # Create user
        user = User.objects.create_user(
            username=username, email=email, password=validated_data.get("password")
        )

        user.save()
        # Save phone number to user profile
        user.profile.phone_number = phone_number
        user.profile.save()
        return user


class EventSerializer(serializers.ModelSerializer):

    registration_link = serializers.ReadOnlyField()
    attendee_count = serializers.SerializerMethodField()
    creator_phone = serializers.SerializerMethodField()
    creator = serializers.ReadOnlyField(source='creator.username')


    class Meta:
        model = Event
        fields = ('id', 'title','flyer','creator', 'description', 'location','time', 'date', 
                  'created_at', 'registration_link', 'attendee_count', 'creator_phone')

    def get_attendee_count(self, obj):
        return obj.attendees.count()
        
    def get_creator_phone(self, obj):
        """Get the phone number of the event creator."""
        try:
            return obj.creator.profile.phone_number
        except ObjectDoesNotExist:
            return None
   

    def create(self, validated_data):
        """Associate the event with the creator."""
        validated_data["creator"] = self.context["request"].user
        return super().create(validated_data)


class EventDetailSerializer(EventSerializer):
    """Serializer for detailed event view."""

    class Meta(EventSerializer.Meta):
        fields = EventSerializer.Meta.fields + ("updated_at",)


class AttendeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendee
        fields = ("id", "name", "email", "phone_number", "registered_at")

    def create(self, validated_data):
        """Associate an attendee with an event."""
        event_id = self.context.get("event_id")
        if not event_id:
            raise serializers.ValidationError({"event_id": "Event ID is required."})

        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise serializers.ValidationError({"event_id": "Event not found."})

        validated_data["event"] = event
        return super().create(validated_data)


class ReminderSerializer(serializers.ModelSerializer):
    """Serializer for reminders."""

    class Meta:
        model = Reminder
        fields = ("id", "sent_at", "message", "type")
