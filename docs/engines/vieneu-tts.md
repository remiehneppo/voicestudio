# VoiceStudio: VieNeu-TTS v3 Turbo

Connect synthesis to a local **VieNeu-TTS v3 Turbo** server exposing an
OpenAI-compatible `POST /v1/audio/speech` endpoint (default port `8004`).
VieNeu-TTS v3 Turbo is optimized for natural Vietnamese speech across Northern,
Central, and Southern accents with 25 built-in preset voices and English
code-switching support.

## Setup

1. Start the VieNeu-TTS server on port `8004` (Docker or local Python).
2. Verify it responds on `GET http://127.0.0.1:8004/health`.
3. Select **VieNeu-TTS v3 Turbo** in **Model Catalogue**, or pin it via
   environment variable:

```bash
export OMNIVOICE_TTS_BACKEND=vieneu-tts
export OMNIVOICE_VIENEU_URL=http://127.0.0.1:8004
```

## Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `OMNIVOICE_VIENEU_URL` | `http://127.0.0.1:8004` | Server origin URL |
| `OMNIVOICE_VIENEU_VOICE` | `Thục Đoan` | Default preset voice name or id |
| `OMNIVOICE_VIENEU_API_KEY` | empty | Optional bearer token (`TTS_API_KEY`) |
