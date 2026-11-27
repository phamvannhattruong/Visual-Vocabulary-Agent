"""Decode browser recordings and prepare WAV audio for pronunciation evaluation."""

import io
import wave
from itertools import chain

import av

MAX_RECORDING_BYTES = 5 * 1024 * 1024
MAX_RECORDING_SECONDS = 30
WAV_SAMPLE_RATE = 16000

_RECORDING_FORMATS = {
    "audio/wav": "wav",
    "audio/wave": "wav",
    "audio/x-wav": "wav",
    "application/octet-stream": "wav",
    "audio/webm": "matroska",
    "audio/ogg": "ogg",
    "audio/mp4": "mov",
    "audio/m4a": "mov",
    "audio/x-m4a": "mov",
}


class InvalidRecording(ValueError):
    """A recording that the learner can correct by recording again."""


def prepare_pronunciation_audio(audio_bytes: bytes, mime_type: str | None) -> bytes:
    media_type = (mime_type or "audio/wav").split(";", 1)[0].strip().lower()
    container_format = _RECORDING_FORMATS.get(media_type)
    if container_format is None:
        raise InvalidRecording("Định dạng ghi âm chưa được hỗ trợ. Hãy thu âm lại trong trình duyệt.")
    if not audio_bytes:
        raise InvalidRecording("Bản ghi đang trống. Hãy thu âm lại.")

    output = io.BytesIO()
    samples = 0
    has_signal = False
    resampler = av.AudioResampler(format="s16", layout="mono", rate=WAV_SAMPLE_RATE)
    try:
        with av.open(io.BytesIO(audio_bytes), format=container_format) as recording, wave.open(output, "wb") as wav:
            if not recording.streams.audio:
                raise InvalidRecording("Bản ghi không có âm thanh. Hãy thu âm lại.")

            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(WAV_SAMPLE_RATE)
            for frame in chain(recording.decode(audio=0), (None,)):
                for converted in resampler.resample(frame):
                    samples += converted.samples
                    if samples > MAX_RECORDING_SECONDS * WAV_SAMPLE_RATE:
                        raise InvalidRecording("Bản ghi quá dài. Hãy thu âm tối đa 30 giây.")
                    pcm = converted.to_ndarray()
                    has_signal = has_signal or bool(pcm.any())
                    wav.writeframesraw(pcm.astype("<i2", copy=False).tobytes())

    except av.error.FFmpegError as exc:
        raise InvalidRecording("Không đọc được bản ghi. Hãy thu âm lại.") from exc

    if not has_signal:
        raise InvalidRecording("Bản ghi không có âm thanh. Hãy thu âm lại.")
    return output.getvalue()
