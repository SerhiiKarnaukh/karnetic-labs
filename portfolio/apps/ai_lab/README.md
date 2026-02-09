# AI Lab

### App on AWS: <https://karnaukh-webdev.com/category/django/ai-lab-back-end/>

### App on Firebase: <https://karnaukh-vue-test.web.app/ai-lab>

![AI Lab screenshot](https://github.com/SerhiiKarnaukh/karnetic-labs/blob/main/portfolio/apps/ai_lab/ai_lab_main.jpg)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [REST API](#rest-api)
  - [Chat](#chat)
  - [Image Generation](#image-generation)
  - [Image Download](#image-download)
  - [Voice Generation](#voice-generation)
  - [Vision Image Upload](#vision-image-upload)
  - [Realtime Token](#realtime-token)
- [Services](#services)
- [Function Calling (Tools)](#function-calling-tools)
- [Utility Functions](#utility-functions)
- [Scheduled Tasks](#scheduled-tasks)
- [Configuration](#configuration)
- [Frontend](#frontend)
- [Testing](#testing)

---

## Overview

**AI Lab** is a pure REST API module powered by the OpenAI platform. It exposes endpoints for conversational chat (GPT-4o with function calling), image generation (DALL-E 3), voice synthesis (GPT-4o Audio Preview), vision image analysis, and Realtime API token provisioning.

The app has **no database models** -- generated files (images, audio) are stored in the media directory and cleaned up daily by a Celery task. All endpoints are publicly accessible (`AllowAny`).

---

## Architecture

```
Vue.js Frontend (Firebase)
       │
       ▼  REST API (JSON)
   AI Lab API Views
       │
       ├── OpenAIService ──── OpenAI API (GPT-4o, DALL-E 3, Audio Preview, Realtime)
       │
       ├── StockAPI ────────── Alpha Vantage API (function calling)
       │
       └── Media Storage
            ├── generated_images/
            ├── generated_voices/
            └── vision_images/
                     │
                     ▼  Celery Beat (daily cleanup)
              delete_generated_media
```

---

## REST API

Base: `/ai-lab/`

All endpoints use Django REST Framework `APIView` with `AllowAny` permission.

### Chat

**`POST /ai-lab/`** -- `AiLabChatView`

Conversational chat with GPT-4o. Supports text prompts, image inputs for vision, and function calling (e.g. stock price lookup).

| Parameter | Type | Required | Description |
|---|---|---|---|
| `question` | string | Yes | User's text prompt |
| `prompt_images` | array of URLs | No | Image URLs for vision input |

**Response:**

```json
{ "message": "AI response text" }
```

**Behavior:**
- System prompt: *"Answer briefly - no more than five sentences and in the form of a joke."*
- When `prompt_images` is provided, builds a multi-part content block with text + image URLs
- Supports function calling -- if GPT-4o invokes a tool (e.g. `get_stock_price`), the view executes it and feeds the result back for a follow-up response
- Returns `500` with error message on failure

---

### Image Generation

**`POST /ai-lab/image-generator/`** -- `AiLabImageGeneratorView`

Generates an image using DALL-E 3, downloads it, and saves it locally.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `question` | string | Yes | Image generation prompt |

**Response:**

```json
{ "message": "https://domain.com/media/generated_images/prompt_text_v1.png" }
```

**Behavior:**
- Generates image via DALL-E 3
- Downloads the resulting image from OpenAI's URL
- Saves to `MEDIA_ROOT/generated_images/` with an auto-versioned filename
- Returns the full public URL to the saved image
- Returns `400` if prompt is missing, `500` on errors

---

### Image Download

**`POST /ai-lab/download-image/`** -- `AiLabImageDownloadView`

Serves a previously generated image as a file download.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `filename` | string | Yes | Name of the image file |

**Response:** `FileResponse` (binary download)

- Returns `400` if filename is missing, `404` if file not found

---

### Voice Generation

**`POST /ai-lab/voice-generator/`** -- `AiLabVoiceGeneratorView`

Generates speech audio from a text prompt using GPT-4o Audio Preview.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `question` | string | Yes | Text prompt for voice generation |

**Response:**

```json
{ "message": "https://domain.com/media/generated_voices/prompt_text_v1.mp3" }
```

**Behavior:**
- Generates audio via GPT-4o Audio Preview (voice: `verse`, format: `mp3`)
- Decodes base64 audio data and saves to `MEDIA_ROOT/generated_voices/`
- Returns the full public URL to the saved audio file
- Returns `400` if prompt is missing, `500` on errors

---

### Vision Image Upload

**`POST /ai-lab/upload-vision-images/`** -- `AiLabVisionImagesUploadView`

Uploads images for subsequent use with the Chat endpoint's vision capability.

| Parameter | Type | Required | Description |
|---|---|---|---|
| `images[]` | file list | Yes | One or more image files (multipart/form-data) |

**Response:**

```json
{ "uploaded_images": ["https://domain.com/media/vision_images/photo1.jpg", "..."] }
```

**Behavior:**
- Saves files to `MEDIA_ROOT/vision_images/`
- Handles filename conflicts by appending a counter suffix
- Returns an array of full URLs to the uploaded images
- Returns `400` if no images are provided

---

### Realtime Token

**`POST /ai-lab/realtime-token/`** -- `AiLabRealtimeTokenView`

Creates an OpenAI Realtime API session token for client-side streaming.

| Parameter | Type | Required | Description |
|---|---|---|---|
| *(none)* | -- | -- | No request body needed |

**Response:** JSON session object from OpenAI (contains ephemeral token)

**Behavior:**
- No authentication required (`authentication_classes = []`)
- Creates a Realtime session with model `gpt-4o-realtime-preview-2024-12-17`, voice `alloy`
- Returns the raw OpenAI session response
- Returns `500` on errors

---

## Services

`services.py` encapsulates all OpenAI API interactions in the `OpenAIService` class:

| Method | Model | API | Description |
|---|---|---|---|
| `get_ai_response(messages, tools)` | gpt-4o | `responses.create()` | Chat completion with function calling support |
| `get_img_gen_response(prompt)` | dall-e-3 | `images.generate()` | Image generation, returns image URL |
| `get_voice_gen_response(prompt)` | gpt-4o-audio-preview | `chat.completions.create()` | Voice synthesis (modalities: text + audio, voice: verse, format: mp3) |

All methods raise descriptive exceptions on failure.

---

## Function Calling (Tools)

The Chat endpoint supports OpenAI function calling. Tools are defined in `tools.py`:

| Tool | Function | Description |
|---|---|---|
| `get_stock_price` | `StockAPI.get_stock_price(symbol)` | Fetches current stock price from Alpha Vantage |

**Parameters:** `symbol` (string, required) -- stock ticker symbol (e.g. `"AAPL"`)

**Flow:**
1. User asks a stock-related question
2. GPT-4o decides to call `get_stock_price` with the detected symbol
3. The view executes `StockAPI.get_stock_price()` via the Alpha Vantage API
4. The result is fed back to GPT-4o for a natural language follow-up

---

## Utility Functions

`utils.py` provides helpers for file management and external APIs:

| Function | Description |
|---|---|
| `StockAPI.get_stock_price(symbol)` | Fetches stock price from Alpha Vantage `GLOBAL_QUOTE` endpoint |
| `generate_file_name_with_extension(prompt, dir, extension)` | Creates a unique filename from a prompt (max 25 chars, auto-versioned) |
| `get_next_version_number(base_file_name, extension, dir)` | Scans directory for existing files and returns next version number |

**Filename format:** `{prompt_text}_v{version}.{extension}` (e.g. `a_sunset_over_mountains_v3.png`)

---

## Scheduled Tasks

| Time (UTC) | Task | Description |
|---|---|---|
| 02:00 | `delete_generated_media` | Deletes all files and subdirectories in `generated_images/`, `generated_voices/`, and `vision_images/` |

---

## Configuration

### Required Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (used by all AI endpoints) |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key (used by stock price tool) |

### Required Django Settings

| Setting | Usage |
|---|---|
| `MEDIA_ROOT` | Base directory for generated files |
| `MEDIA_URL` | Public URL prefix for media files |

### Media Directories

| Directory | Content |
|---|---|
| `generated_images/` | DALL-E 3 generated images (PNG) |
| `generated_voices/` | GPT-4o Audio generated voice files (MP3) |
| `vision_images/` | User-uploaded images for vision processing |

---

## Frontend

The AI Lab frontend is a separate **Vue.js** application deployed on Firebase.

- **Vue.js frontend**: <https://karnaukh-vue-test.web.app/ai-lab>
- **Project page**: <https://karnaukh-webdev.com/category/vuejs/ai-lab-front-end/>

The frontend consumes the REST API directly. No authentication is required for any endpoint.

---

## Testing

Tests are located in the `tests/` directory:

| Test File | Coverage |
|---|---|
| `test_api.py` | Chat (text, vision, function calling, errors), Image generation (success, missing prompt, download failures), Image download (success, missing filename, 404), Voice generation (success, missing prompt, errors), Vision upload (success, no images) |
| `test_services.py` | OpenAIService constructor, `get_ai_response` (success, exception), `get_img_gen_response` (success, exception), `get_voice_gen_response` (success, exception) |
| `test_utils.py` | `StockAPI.get_stock_price` (success, missing key, connection error), `generate_file_name_with_extension` (initial version, increment), `get_next_version_number` (missing dir, irrelevant files) |

Run tests:

```bash
make test
```
