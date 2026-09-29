from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import sales
from .service.ai_service import ask_database



#Health Endpoint

@api_view(['GET'])
def health(request):
    return Response({"status": "ok"})


#Data Through API

@api_view(['POST'])
def ask_ai(request):
    data = request.data.get("user_query")

    if not data:
        return Response({"status": "error"},status=status.HTTP_400_BAD_REQUEST)
    result = ask_database(data)
    return Response(result)








