import io
import json
import struct
import unittest
import wave
from unittest.mock import patch

import av
import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ReadTimeout
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.api.routes import learning
from backend.app.db import crud
from backend.app.db.base import Base
from backend.app.db.models import PronunciationLog
from backend.app.services.agents.voice import VoiceAgent


class TestPronunciation(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(learning.router, prefix="/api/v1")
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.voice_agent = object.__new__(VoiceAgent)

    @staticmethod
    def wav_recording(sample=500):
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            wav.writeframes(struct.pack("<hh", sample, -sample) * 800)
        return buffer.getvalue()

    def evaluate(self, audio, media_type="audio/wav", target_word=" bottle "):
        return self.client.post(
            "/api/v1/evaluate-pronunciation",
            data={"target_word": target_word, "user_id": "7"},
            files={"audio_file": ("recording", audio, media_type)},
        )

    @staticmethod
    def model_result(phones):
        return json.dumps({"phones": phones})

    def test_valid_zero_is_returned_and_saved(self):
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        self.addCleanup(engine.dispose)
        Base.metadata.create_all(engine)
        sessions = sessionmaker(bind=engine)
        model_result = self.model_result(["K", "UW", "P"])
        with (
            patch.object(learning, "get_voice_agent", return_value=self.voice_agent),
            patch.object(self.voice_agent, "generate_response", return_value=model_result),
            patch.object(crud, "SessionLocal", sessions),
        ):
            response = self.evaluate(self.wav_recording())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["score"], 0)
        with sessions() as db:
            saved = db.query(PronunciationLog).one()
            self.assertEqual((saved.target_word, saved.score, saved.user_id), ("bottle", 0, 7))

    def test_browser_formats_are_decoded_and_resent_as_wav(self):
        for media_type, container_format, codec in (
            ("audio/webm;codecs=opus", "webm", "libopus"),
            ("audio/mp4", "mp4", "aac"),
        ):
            with self.subTest(media_type=media_type):
                data = io.BytesIO()
                with av.open(data, mode="w", format=container_format) as recording:
                    stream = recording.add_stream(codec, rate=48000)
                    stream.layout = "mono"
                    time = np.arange(4800) / 48000
                    samples = (4000 * np.sin(2 * np.pi * 440 * time)).astype(np.int16)[None, :]
                    frame = av.AudioFrame.from_ndarray(samples, format="s16", layout="mono")
                    frame.sample_rate = 48000
                    for packet in stream.encode(frame) + stream.encode(None):
                        recording.mux(packet)

                with (
                    patch.object(learning, "get_voice_agent", return_value=self.voice_agent),
                    patch.object(
                        self.voice_agent,
                        "generate_response",
                        return_value=self.model_result(["B", "AA", "T", "AX", "L"]),
                    ) as generate,
                    patch.object(learning, "background_save_pronunciation_log"),
                ):
                    response = self.evaluate(data.getvalue(), media_type)

                self.assertEqual(response.status_code, 200, response.text)
                part = generate.call_args.kwargs["contents"][1]
                self.assertEqual(part["mime_type"], "audio/wav")
                with wave.open(io.BytesIO(part["data"]), "rb") as decoded:
                    self.assertEqual((decoded.getnchannels(), decoded.getframerate()), (1, 16000))
                    self.assertGreater(decoded.getnframes(), 0)

    def test_invalid_or_silent_audio_is_rejected_before_model_call(self):
        for audio, media_type in (
            (b"", "audio/wav"),
            (b"invalid recording", "audio/wav"),
            (self.wav_recording(0), "audio/wav"),
            (self.wav_recording(), "application/json"),
        ):
            with (
                self.subTest(media_type=media_type),
                patch.object(learning, "get_voice_agent") as get_agent,
                patch.object(learning, "background_save_pronunciation_log") as save,
            ):
                response = self.evaluate(audio, media_type)
                self.assertEqual(response.status_code, 422, response.text)
                get_agent.assert_not_called()
                save.assert_not_called()

    def test_model_errors_never_save_a_pronunciation_score(self):
        for output, error, status in (
            ("{}", None, 502),
            ("invalid JSON", None, 502),
            (self.model_result(True), None, 502),
            (self.model_result(["UNKNOWN_PHONE"]), None, 502),
            (self.model_result(None), None, 422),
            (self.model_result([]), None, 422),
            (None, ReadTimeout("provider timed out"), 504),
            (None, RuntimeError("provider unavailable"), 502),
        ):
            with (
                self.subTest(output=output, error=error),
                patch.object(learning, "get_voice_agent", return_value=self.voice_agent),
                patch.object(self.voice_agent, "generate_response", return_value=output, side_effect=error),
                patch.object(learning, "background_save_pronunciation_log") as save,
            ):
                response = self.evaluate(self.wav_recording())
                self.assertEqual(response.status_code, status, response.text)
                self.assertNotIn("score", response.json())
                save.assert_not_called()

    def test_general_pronunciation_compares_phones_before_saving_the_score(self):
        for target, heard, score, feedback in (
            ("cup", ["K", "AH", "P"], 100, "khớp"),
            ("cup", ["K", "UW", "P"], 67, "/u/ ở chỗ cần âm /ʌ/"),
            ("ship", ["SH", "IY", "P"], 67, "/i/ ở chỗ cần âm /ɪ/"),
            ("pen", ["P", "EH"], 67, "Chưa nghe thấy âm /n/"),
            ("cat", ["K", "AE", "T", "AX"], 74, "âm thừa /ə/"),
            ("read", ["R", "EH", "D"], 100, "khớp"),
            ("read", ["R", "IY", "D"], 100, "khớp"),
            ("cell phone", ["S", "EH", "L", "F", "OW", "N"], 100, "khớp"),
        ):
            with (
                self.subTest(target=target, heard=heard),
                patch.object(learning, "get_voice_agent", return_value=self.voice_agent),
                patch.object(
                    self.voice_agent, "generate_response",
                    return_value=self.model_result(heard),
                ) as generate,
                patch.object(learning, "background_save_pronunciation_log") as save,
            ):
                response = self.evaluate(self.wav_recording(), target_word=target)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()["score"], score)
                self.assertIn(feedback, response.json()["feedback"])
                self.assertEqual(save.call_args.kwargs["score"], score)
                self.assertNotIn(f'"{target}"', generate.call_args.kwargs["contents"][0])

    def test_word_without_a_reference_does_not_create_a_score(self):
        with (
            patch.object(learning, "get_voice_agent", return_value=self.voice_agent),
            patch.object(self.voice_agent, "generate_response") as generate,
            patch.object(learning, "background_save_pronunciation_log") as save,
        ):
            response = self.evaluate(self.wav_recording(), target_word="zzvqz")

        self.assertEqual(response.status_code, 422)
        self.assertIn("phiên âm tham chiếu", response.json()["detail"])
        generate.assert_not_called()
        save.assert_not_called()
