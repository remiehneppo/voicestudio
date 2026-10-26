"""Unit tests for VieNeuTTSBackend (OpenAI-compatible Vietnamese TTS server)."""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))


def _minimal_wav_24k() -> bytes:
    riff_size = struct.pack("<I", 36 + 2)
    fmt_chunk = struct.pack("<IHHIIHH", 16, 1, 1, 24000, 48000, 2, 16)
    data_size = struct.pack("<I", 2)
    return b"RIFF" + riff_size + b"WAVEfmt " + fmt_chunk + b"data" + data_size + b"\x00\x00"


class _ByteResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return self._payload


def test_vieneu_registered_in_tts_registry():
    from services import tts_backend

    assert "vieneu-tts" in tts_backend._REGISTRY
    assert tts_backend.get_backend_class("vieneu-tts") is tts_backend.VieNeuTTSBackend


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("http://127.0.0.1:8004", "http://127.0.0.1:8004"),
        ("http://127.0.0.1:8004/", "http://127.0.0.1:8004"),
        ("http://127.0.0.1:8004/v1", "http://127.0.0.1:8004"),
        ("http://127.0.0.1:8004/v1/", "http://127.0.0.1:8004"),
        ("http://127.0.0.1:8004/v1/audio/speech", "http://127.0.0.1:8004"),
    ],
)
def test_vieneu_resolve_origin_normalizes_subpaths(monkeypatch, raw, expected):
    from services.tts_backend import VieNeuTTSBackend

    monkeypatch.setenv("OMNIVOICE_VIENEU_URL", raw)
    assert VieNeuTTSBackend._resolve_origin() == expected


def test_vieneu_is_available_probes_health(monkeypatch):
    from services import outbound_http
    from services.tts_backend import VieNeuTTSBackend

    calls = []
    monkeypatch.setenv("OMNIVOICE_VIENEU_URL", "http://127.0.0.1:8004/v1")
    monkeypatch.setenv("OMNIVOICE_VIENEU_API_KEY", "secret-token")
    monkeypatch.setattr(
        outbound_http,
        "open_trusted_endpoint",
        lambda url, **kw: calls.append((url, kw)) or _ByteResponse(b'{"status":"ok"}'),
    )

    ok, msg = VieNeuTTSBackend.is_available()
    assert ok is True
    assert "VieNeu" in msg
    assert calls == [
        (
            "http://127.0.0.1:8004",
            {
                "method": "GET",
                "path": "health",
                "timeout": 2,
                "authorization": "Bearer secret-token",
            },
        )
    ]


def test_vieneu_generate_posts_openai_speech_request(monkeypatch):
    from services import outbound_http
    from services.tts_backend import VieNeuTTSBackend

    captured = []
    wav_bytes = _minimal_wav_24k()

    def fake_open(url, **kw):
        captured.append((url, kw, json.loads(kw["body"].decode("utf-8"))))
        return _ByteResponse(wav_bytes)

    monkeypatch.setenv("OMNIVOICE_VIENEU_URL", "http://127.0.0.1:8004")
    monkeypatch.delenv("OMNIVOICE_VIENEU_VOICE", raising=False)
    monkeypatch.delenv("OMNIVOICE_VIENEU_API_KEY", raising=False)
    monkeypatch.setattr(outbound_http, "open_trusted_endpoint", fake_open)

    backend = VieNeuTTSBackend()
    wav = backend.generate("Xin chào Việt Nam", language="vi", voice="mai_anh", speed=1.25)

    assert wav.shape == (1, 1)
    assert len(captured) == 1
    url, kw, body = captured[0]
    assert url == "http://127.0.0.1:8004"
    assert kw["method"] == "POST"
    assert kw["path"] == "v1/audio/speech"
    assert kw["content_type"] == "application/json"
    assert body == {
        "model": "vieneu-v3-turbo",
        "input": "Xin chào Việt Nam",
        "voice": "Mai Anh",
        "response_format": "wav",
        "speed": 1.25,
    }


def test_vieneu_rejects_empty_and_unsupported_language(monkeypatch):
    from services import outbound_http
    from services.tts_backend import TTSInputError, VieNeuTTSBackend

    monkeypatch.setattr(
        outbound_http,
        "open_trusted_endpoint",
        lambda *_a, **_kw: pytest.fail("Should not make network call"),
    )
    backend = VieNeuTTSBackend()
    with pytest.raises(TTSInputError):
        backend.generate("   ", language="vi")
    with pytest.raises(ValueError, match="doesn't support"):
        backend.generate("Czesc", language="pl")
