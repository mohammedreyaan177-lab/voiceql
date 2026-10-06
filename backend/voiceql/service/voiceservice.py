import logging
from faster_whisper import WhisperModel

logger = logging.getLogger("voiceql")

try:
    model = WhisperModel(
        "small",
        device="cpu",
        compute_type="int8"
    )
    logger.info("Whisper initialized")
except Exception as e:
    logger.critical(f"Whisper init failed: {e}")
    raise


def transcribe_audio(audio_path):
    try:
        segments, info = model.transcribe(audio_path)

        text = " ".join(
            segment.text
            for segment in segments
        )

        logger.info("Transcription completed")
        return text.strip()
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise