from rest_framework.decorators import api_view
from django.http import JsonResponse



@api_view(["GET"])
def Homeroute(request):
    return JsonResponse({"message": " Welcome to Eventrio Official API"})