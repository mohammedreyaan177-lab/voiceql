from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .service.ai_service import ask_database
from .service.voiceservice import transcribe_audio


#Health Endpoint

@api_view(['GET'])
def health(request):
    return Response({"status": "ok"})


#Data Through API
@api_view(['POST'])
def ask_ai(request):
    try:
        data = request.data.get("user_query")

        print(f"POST /ask user_query={data!r}", flush=True)

        if not data:
            return Response({"status": "error"},status=status.HTTP_400_BAD_REQUEST)
        result = ask_database(data)
        print(f"POST /ask result={str(result)[:200]!r}", flush=True)
        return Response(result)
    except Exception as exc:
        print(f"POST /ask failed: {exc!r}", flush=True)
        return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#Voice endpoint.

@api_view(["POST"])
def voice_query(request):

    try:
        audio = request.FILES.get("audio")

        if not audio:
            return Response({
                "error": "Audio file is required"
            }, status=400)

        print(f"POST /voice audio={audio.name!r}", flush=True)

        audio_path = f"temp_{audio.name}"

        with open(audio_path, "wb+") as destination:

            for chunk in audio.chunks():
                destination.write(chunk)

        text = transcribe_audio(audio_path)

        print(f"POST /voice text={text!r}", flush=True)

        return Response({
            "text": text
        })
    except Exception as exc:
        print(f"POST /voice failed: {exc!r}", flush=True)
        return Response({"error": str(exc)}, status=500)





