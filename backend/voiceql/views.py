import os
import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .service.ai_service import ask_database
from .service.voiceservice import transcribe_audio

logger = logging.getLogger("voiceql")


# Health Endpoint

@api_view(['GET'])
def health(request):
    return Response({"status": "ok"})


# Data Through API
@api_view(['POST'])
def ask_ai(request):
    try:
        data = request.data.get("user_query")

        logger.info(f"POST /ask query={data!r}")

        if not data:
            logger.warning("POST /ask empty query")
            return Response({"status": "error"}, status=status.HTTP_400_BAD_REQUEST)

        result = ask_database(data)
        logger.info("POST /ask success")
        return Response(result)

    except Exception as exc:
        logger.error(f"POST /ask failed: {exc}")
        return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Voice endpoint.

@api_view(["POST"])
def voice_query(request):
    audio_path = None
    try:
        audio = request.FILES.get("audio")

        if not audio:
            logger.warning("POST /voice no file")
            return Response({
                "error": "Audio file is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"POST /voice file={audio.name!r}")

        audio_path = f"temp_{audio.name}"

        with open(audio_path, "wb+") as destination:
            for chunk in audio.chunks():
                destination.write(chunk)

        text = transcribe_audio(audio_path)

        logger.info("POST /voice success")

        return Response({
            "text": text
        })

    except Exception as exc:
        logger.error(f"POST /voice failed: {exc}")
        return Response({"error": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    finally:
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception as e:
                logger.error(f"Temp file cleanup failed: {e}")