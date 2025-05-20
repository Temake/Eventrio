from django.http import JsonResponse

def root(request):
    return JsonResponse( {
        "message": "Welcome to the Event Management API",
        "version": "1.0.0",
        "endpoints": {
            "auth": {
                "/auth/register": {
                    "method": "POST",
                    "description": "Register a new user",
                    "required_fields": ["username", "email", "password"],
                    "optional_fields": ["full_name", "phone_number"]
                },
                "/auth/login": {
                    "method": "POST",
                    "description": "Login and get access token",
                    "required_fields": ["email", "password"]
                },
                "/auth/refresh": {
                    "method": "POST",
                    "description": "Refresh access token",
                    "required_fields": ["refresh_token"]
                }
            },
            "events": {
                "/events": {
                    "GET": "List all events or filter by query parameters",
                    "POST": "Create a new event (requires authentication)"
                },
                "/events/{event_id}": {
                    "GET": "Get specific event details",
                    "PUT": "Update event (requires ownership)",
                    "DELETE": "Delete event (requires ownership)"
                },
                "/events/my-events": {
                    "GET": "List events created by authenticated user"
                }
            },
            "registrations": {
                "/registrations/{event_id}": {
                    "POST": "Register for an event",
                    "required_fields": ["attendee_name", "email"],
                    "optional_fields": ["phone_number"]
                },
                "/registrations/my-registrations": {
                    "GET": "List events user has registered for (requires authentication)"
                }
            },
            "users": {
                "/users/profile": {
                    "GET": "Get authenticated user profile",
                    "PUT": "Update user profile"
                }
            }
        },
       
    })
