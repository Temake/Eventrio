# Event Management API

A comprehensive Django REST Framework application for creating, managing, and attending events with smart WhatsApp integration.

## Overview

This Event Management API allows users to create events, generate registration links, manage attendees, and implement automated reminders via email and WhatsApp. It also includes a WhatsApp integration with Google's Gemini AI model that can answer attendee questions based on event descriptions.

## Features

- **User Authentication**: Register and manage user accounts with phone number support
- **Event Management**: Create, read, update, and delete events
- **Event Registration**: Generate unique links for attendees to register for events
- **Attendee Management**: Track and manage event attendees
- **Automated Reminders**: Send scheduled reminders via email and WhatsApp as events approach
- **WhatsApp Integration**: Answer questions about events using Google Gemini AI
- **Public Event Listing**: View all available events

## Technology Stack

- **Backend**: Django 4.2+ and Django REST Framework
- **Database**: PostgreSQL (recommended)
- **Task Queue**: Celery with Redis for background tasks and scheduled reminders
- **External APIs**:
  - WhatsApp Business API for messaging
  - Google Gemini AI for natural language processing

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL
- Redis

### Setup

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/event-management-api.git
cd event-management-api
```

2. **Create and activate a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create a `.env` file in the project root and add:

```env
# Django
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://user:password@localhost:5432/eventdb

# Email
EMAIL_HOST=smtp.yourmailprovider.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=events@yourdomain.com

# WhatsApp API
WHATSAPP_API_URL=https://your-whatsapp-api-endpoint.com/v1/messages
WHATSAPP_API_TOKEN=your_whatsapp_api_token

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

5. **Set up the database**

```bash
python manage.py migrate
```

6. **Create a superuser**

```bash
python manage.py createsuperuser
```

## Running the Application

1. **Start the Django development server**

```bash
python manage.py runserver
```

2. **Start Celery worker**

```bash
celery -A main worker -l info
```

3. **Start Celery beat for scheduled tasks**

```bash
celery -A main beat -l info
```

## API Endpoints

### Authentication

- `POST /api/register/` - Register a new user with phone number
-`POST /api/login/` - Login a user 

### Events

- `GET /api/events/` - List events created by the authenticated user
- `POST /api/events/` - Create a new event
- `GET /api/events/{id}/` - Get details of a specific event
- `PUT /api/events/{id}/` - Update an event
- `DELETE /api/events/{id}/` - Delete an event
- `GET /api/events/{id}/attendees/` - List attendees for a specific event
- `GET /api/public-events/` - List all public events

### Registration

- `GET /api/register-event/{registration_link}/` - View event details for registration
- `POST /api/register-event/{registration_link}/` - Register for an event as an attendee

### WhatsApp Integration

The WhatsApp integration is handled via webhooks that are configured with your WhatsApp Business API provider. These webhooks will process incoming messages, interact with the Gemini AI, and deliver responses back to users.

## Usage Examples

### Creating a New Event

```bash
curl -X POST http://localhost:8000/api/events/ \
  -H "Authorization: Bearer {your_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "TechyJaunty 2025",
    "description": "Annual technology conference showcasing the latest innovations",
    "location": "Obafemi Awolowo University",
    "date": "2025-06-15T09:00:00Z"
  }'
```

### Registering for an Event

```bash
curl -X POST http://localhost:8000/api/register-event/abc123-xyz456/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone_number": "+1234567890"
  }'
```

## WhatsApp Integration Setup

To set up the WhatsApp integration:

1. Register with a WhatsApp Business API provider
2. Configure your webhook URL to point to your application's WhatsApp webhook endpoint
3. Set up the necessary environment variables for the WhatsApp API
4. Configure Google Gemini AI with your API key

## Scheduled Reminders

The application uses Celery to send automated reminders to attendees:

- 3 days before the event
- 1 day before the event

Reminders are sent via both email and WhatsApp (if a phone number is provided).
