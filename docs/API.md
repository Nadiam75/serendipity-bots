# API reference (backend integration)

Base URL (VPS / Laravel): `http://127.0.0.1:8001`  
Base URL (local): `http://127.0.0.1:8001`

**Live VPS examples:** see [`docs/vps-live-examples.md`](vps-live-examples.md) (real curl I/O from production test).

All `POST` bodies are `Content-Type: application/json`.

**Stateless design:** chat history is **not** stored by this service. Your backend (e.g. Laravel) loads prior turns from the database and sends them on each request.

**Contracts:** question types, layouts, and example shapes live in `contracts.json`. Fetch them at runtime via `GET /v1/contracts`.

---

## Endpoint index

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness check |
| `GET` | `/v1/contracts` | Question modes, types, examples |
| `GET` | `/v1/bots` | List available bots / capabilities |
| `POST` | `/v1/bots/teacher/chat` | Teacher chat (open questions) |
| `POST` | `/v1/bots/story/chat` | Story chat (MCQ / story context) |
| `POST` | `/v1/bots/assess` | Score a child's answer |
| `POST` | `/v1/bots/generate-exercises` | Generate similar exercises |
| `POST` | `/v1/bots/fun-fact` | Generate a fun fact from interests |
| `POST` | `/v1/chat/completions` | Legacy OpenAI-shaped chat |
| `POST` | `/v1/assess` | Legacy alias of assess |
| `POST` | `/v1/fun-fact` | Legacy alias of fun-fact |

Interactive docs: `GET /docs`

---

## 1. `GET /health`

No request body.

**Response `200`**

```json
{
  "status": "ok"
}
```

---

## 2. `GET /v1/contracts`

No request body. Returns the full `contracts.json` payload.

**Response `200`** (abbreviated)

```json
{
  "schema_version": "1.1",
  "question_modes": {
    "convergent": {
      "label_fa": "همگرا",
      "description_fa": "سؤال با گزینه و پاسخ مشخص (چندگزینه‌ای)",
      "layouts": ["multiple_choice", "image_multiple_choice"]
    },
    "divergent": {
      "label_fa": "واگرا",
      "description_fa": "سؤال باز و تشریحی",
      "layouts": ["question"]
    }
  },
  "question_types": [
    {
      "id": "mcq_single",
      "label_fa": "چندگزینه‌ای (یک پاسخ)",
      "question_mode": "convergent",
      "layout": "multiple_choice",
      "exercise_type": "mcq",
      "min_selections": 1,
      "max_selections": 1,
      "recommended_bot": "story",
      "assess_mode": "mcq"
    }
  ],
  "examples": [
    {
      "question_type_id": "mcq_single",
      "story_page": { "type": "exercise", "title": "سؤال", "text": "...", "meta": { "layout": "multiple_choice", "question_mode": "convergent" } },
      "exercise": { "type": "mcq", "question": "...", "options": [], "correct_option_ids": [], "order": 1, "is_required": true }
    }
  ]
}
```

**`question_type_id` values:** `mcq_single` | `mcq_multi` | `open_question` | `image_mcq`

---

## 3. `GET /v1/bots`

No request body.

**Response `200`**

```json
[
  {
    "id": "teacher",
    "name": "زال",
    "description": "همراه مهربان — کمک در پاسخ تشریحی، جمله‌سازی، و گفتگوی آموزشی",
    "chat_url": "/v1/bots/teacher/chat",
    "assess_url": null,
    "generate_url": null,
    "fun_fact_url": null
  },
  {
    "id": "story",
    "name": "زال — داستان",
    "description": "کمک در درک داستان، احساس شخصیت‌ها، نشانه‌ها، و سؤال‌های مرتبط با متن",
    "chat_url": "/v1/bots/story/chat",
    "assess_url": null,
    "generate_url": null,
    "fun_fact_url": null
  },
  {
    "id": "assess",
    "name": "ارزیاب پاسخ",
    "description": "ارزیابی پاسخ کودک (همگرا/واگرا) نسبت به objectives",
    "chat_url": null,
    "assess_url": "/v1/bots/assess",
    "generate_url": null,
    "fun_fact_url": null
  },
  {
    "id": "generate",
    "name": "تولید تمرین",
    "description": "ساخت سؤال‌های مشابه از سؤال و پاسخ مرجع",
    "chat_url": null,
    "assess_url": null,
    "generate_url": "/v1/bots/generate-exercises",
    "fun_fact_url": null
  },
  {
    "id": "fun-fact",
    "name": "حقیقت جالب",
    "description": "ساخت یک حقیقت جالب و ساده بر اساس علایق کودک",
    "chat_url": null,
    "assess_url": null,
    "generate_url": null,
    "fun_fact_url": "/v1/bots/fun-fact"
  }
]
```

---

## 4. `POST /v1/bots/{bot_id}/chat`

**`bot_id`:** `teacher` | `story`

Your backend sends the **current** user message in `message` and **prior** turns in `history` (oldest first). Do **not** include the current message in `history`.

### Request — first message

```json
{
  "message": "اگر ۳ تا سیب داشته باشی و ۲ تا دیگر بهت بدهند، حالا چند تا سیب داری؟",
  "history": []
}
```

### Request — follow-up (with history from your DB)

```json
{
  "message": "۵ تا سیب دارم",
  "history": [
    {
      "role": "user",
      "content": "اگر ۳ تا سیب داشته باشی و ۲ تا دیگر بهت بدهند، حالا چند تا سیب داری؟"
    },
    {
      "role": "assistant",
      "content": "عالیه! بیا با هم حساب کنیم: ۳ تا سیب داشتی و ۲ تا دیگر گرفتی..."
    }
  ]
}
```

### Optional request fields

| Field | Type | Description |
|-------|------|-------------|
| `user_prompt` | string | Extra instructions merged into the bot system prompt |
| `model` | string | Upstream model id (default from server env) |
| `max_output_tokens` | int | Cap on generated tokens |

### Response `200`

```json
{
  "bot_id": "teacher",
  "reply": "آفرین! درست گفتی. ۳ تا سیب داشتی و ۲ تا دیگر گرفتی، پس حالا ۵ تا سیب داری.",
  "model": "deepseek-v4-flash",
  "history_turns_used": 1
}
```

| Field | Description |
|-------|-------------|
| `bot_id` | Which bot answered (`teacher` or `story`) |
| `reply` | Assistant text in Persian (show to the child) |
| `model` | Model used upstream |
| `history_turns_used` | Number of prior turns sent after server-side trimming |

---

## 5. `POST /v1/bots/assess`

Scores the child's answer against learning objectives. Use `question_type_id` from contracts when possible — the server auto-fills `question_mode`, `assess_mode`, `layout`, and selection limits.

### 5a. MCQ (single answer) — `question_type_id: mcq_single`

**Request**

```json
{
  "question_type_id": "mcq_single",
  "question": "اگر ۳ تا سیب داشته باشی و ۲ تا دیگر بهت بدهند، حالا چند تا سیب داری؟",
  "selected_option_ids": ["b"],
  "correct_option_ids": ["b"],
  "options": [
    { "id": "a", "label": "۴" },
    { "id": "b", "label": "۵" },
    { "id": "c", "label": "۶" },
    { "id": "d", "label": "۷" }
  ],
  "areas": [
    {
      "name": "ریاضی",
      "sub_areas": [
        {
          "name": "جمع ساده",
          "objectives": [
            "کودک بتواند دو عدد کوچک را با هم جمع کند",
            "کودک گزینه درست را انتخاب کند"
          ]
        }
      ]
    }
  ],
  "interests": ["میوه", "بازی"]
}
```

For MCQ: `selected_option_ids` is **required**. `answer` is optional.

**Response `200`**

```json
{
  "question_mode": "convergent",
  "question_type_id": "mcq_single",
  "assess_mode": "mcq",
  "assessments": [
    {
      "area": "ریاضی",
      "sub_area": "جمع ساده",
      "objective": "کودک بتواند دو عدد کوچک را با هم جمع کند",
      "status": "met",
      "score": 5,
      "feedback": "کودک جمع ۳ و ۲ را درست انجام داده است."
    },
    {
      "area": "ریاضی",
      "sub_area": "جمع ساده",
      "objective": "کودک گزینه درست را انتخاب کند",
      "status": "met",
      "score": 5,
      "feedback": "گزینه ۵ را به‌درستی انتخاب کرده است."
    }
  ],
  "overall_score": 5,
  "score_segment": "پیشرو",
  "summary": "پاسخ کودک کاملاً درست است و هر دو هدف یادگیری برآورده شده‌اند."
}
```

### 5b. Open question — `question_type_id: open_question`

**Request**

```json
{
  "question_type_id": "open_question",
  "question": "اگر جای شخصیت اصلی داستان بودی چه کاری انجام می‌دادی؟",
  "answer": "من با دوستم صحبت می‌کردم و کمکش می‌کردم.",
  "answer_count": 1,
  "max_words_per_answer": 120,
  "answer_placeholders": ["پاسخت را اینجا بنویس..."],
  "areas": [
    {
      "name": "درک مطلب",
      "sub_areas": [
        {
          "name": "همدلی",
          "objectives": [
            "کودک پاسخی مرتبط با احساس شخصیت بدهد",
            "کودک دلیل کوتاهی برای انتخاب خود بیان کند"
          ]
        }
      ]
    }
  ]
}
```

For open questions: `answer` is **required**.

**Response `200`**

```json
{
  "question_mode": "divergent",
  "question_type_id": "open_question",
  "assess_mode": "open",
  "assessments": [
    {
      "area": "درک مطلب",
      "sub_area": "همدلی",
      "objective": "کودک پاسخی مرتبط با احساس شخصیت بدهد",
      "status": "met",
      "score": 5,
      "feedback": "پاسخ با موضوع کمک و همدلی هماهنگ است."
    },
    {
      "area": "درک مطلب",
      "sub_area": "همدلی",
      "objective": "کودک دلیل کوتاهی برای انتخاب خود بیان کند",
      "status": "partial",
      "score": 3,
      "feedback": "اقدام کودک مشخص است اما دلیل کوتاهی بیان نشده."
    }
  ],
  "overall_score": 4,
  "score_segment": "پیشرو",
  "summary": "پاسخ مناسب است؛ می‌توان با یک سؤال پیگیری، دلیل را کامل‌تر کرد."
}
```

### 5c. Image MCQ — `question_type_id: image_mcq`

**Request**

```json
{
  "question_type_id": "image_mcq",
  "question": "سه تصویر مرتبط با داستان را انتخاب کن.",
  "selected_option_ids": ["image-1", "image-2", "image-4"],
  "correct_option_ids": ["image-1", "image-2", "image-3"],
  "options": [
    { "id": "image-1", "image_path": "images/generated/image-1.png", "alt": "توضیح تصویر اول" },
    { "id": "image-2", "image_path": "images/generated/image-2.png", "alt": "توضیح تصویر دوم" },
    { "id": "image-3", "image_path": "images/generated/image-3.png", "alt": "توضیح تصویر سوم" },
    { "id": "image-4", "image_path": "images/generated/image-4.png", "alt": "توضیح تصویر چهارم" }
  ],
  "min_selections": 3,
  "max_selections": 3,
  "areas": [
    {
      "name": "درک مطلب",
      "sub_areas": [
        {
          "name": "نشانه‌های داستان",
          "objectives": ["کودک تصاویر مرتبط با داستان را تشخیص دهد"]
        }
      ]
    }
  ]
}
```

### Assess response fields

| Field | Description |
|-------|-------------|
| `question_mode` | `convergent` or `divergent` |
| `question_type_id` | Echo of request (if provided) |
| `assess_mode` | `mcq` or `open` |
| `assessments[]` | One item per objective |
| `assessments[].status` | `met` \| `partial` \| `not_met` |
| `assessments[].score` | Integer `0`–`5` |
| `assessments[].feedback` | Short Persian note for teachers |
| `overall_score` | Rounded mean of objective scores (`0`–`5`) |
| `score_segment` | From `overall_score`: `0–1` → `نوآموز`, `2–3` → `توانمند`, `4–5` → `پیشرو` |
| `summary` | Overall Persian summary for teachers |

**Legacy alias:** `POST /v1/assess` — same request/response body.

---

## 6. `POST /v1/bots/generate-exercises`

Creates new exercises similar to a source question + answer. Output shape matches `contracts.json` → `examples[]`.

### Request — MCQ single

```json
{
  "question_type_id": "mcq_single",
  "question": "اگر ۳ تا سیب داشته باشی و ۲ تا دیگر بهت بدهند، حالا چند تا سیب داری؟",
  "answer": "۵",
  "count": 2,
  "interests": ["میوه"]
}
```

### Request — open question

```json
{
  "question_type_id": "open_question",
  "question": "اگر جای شخصیت اصلی داستان بودی چه کاری انجام می‌دادی؟",
  "answer": "با دوستم صحبت می‌کردم و کمکش می‌کردم.",
  "count": 1,
  "answer_count": 1,
  "max_words_per_answer": 120,
  "answer_placeholders": ["پاسخت را اینجا بنویس..."]
}
```

### Response `200` (MCQ example, abbreviated)

```json
{
  "schema_version": "1.1",
  "source_question": "اگر ۳ تا سیب داشته باشی و ۲ تا دیگر بهت بدهند، حالا چند تا سیب داری؟",
  "question_type_id": "mcq_single",
  "question_mode": "convergent",
  "exercises": [
    {
      "question_type_id": "mcq_single",
      "story_page": {
        "type": "exercise",
        "title": "سؤال",
        "text": "اگر ۴ تا پرتقال داشته باشی و ۱ تا دیگر بهت بدهند، حالا چند تا پرتقال داری؟",
        "image_path": null,
        "meta": {
          "layout": "multiple_choice",
          "question_mode": "convergent",
          "min_selections": 1,
          "max_selections": 1,
          "answer_count": null,
          "max_words_per_answer": null,
          "max_characters_per_answer": null,
          "answer_placeholders": null
        }
      },
      "exercise": {
        "type": "mcq",
        "question": "اگر ۴ تا پرتقال داشته باشی و ۱ تا دیگر بهت بدهند، حالا چند تا پرتقال داری؟",
        "options": [
          { "id": "a", "label": "۳", "alt": null, "image_path": null },
          { "id": "b", "label": "۵", "alt": null, "image_path": null },
          { "id": "c", "label": "۶", "alt": null, "image_path": null }
        ],
        "correct_option_ids": ["b"],
        "order": 1,
        "is_required": true
      },
      "sample_answer": null
    }
  ],
  "model": "deepseek-v4-flash"
}
```

### Response `200` (open question example, abbreviated)

```json
{
  "schema_version": "1.1",
  "source_question": "اگر جای شخصیت اصلی داستان بودی چه کاری انجام می‌دادی؟",
  "question_type_id": "open_question",
  "question_mode": "divergent",
  "exercises": [
    {
      "question_type_id": "open_question",
      "story_page": {
        "type": "exercise",
        "title": "سؤال",
        "text": "اگر دوستت ناراحت بود، چه کار می‌کردی؟",
        "image_path": null,
        "meta": {
          "layout": "question",
          "question_mode": "divergent",
          "min_selections": null,
          "max_selections": null,
          "answer_count": 1,
          "max_words_per_answer": 120,
          "max_characters_per_answer": null,
          "answer_placeholders": ["پاسخت را اینجا بنویس..."]
        }
      },
      "exercise": null,
      "sample_answer": "با او صحبت می‌کردم و سعی می‌کردم او را دلداری بدهم."
    }
  ],
  "model": "deepseek-v4-flash"
}
```

| Field | Description |
|-------|-------------|
| `exercises[]` | Contract-shaped items — store directly or map to your DB |
| `exercises[].exercise` | `null` for open questions; MCQ object for convergent types |
| `exercises[].sample_answer` | Model answer for open questions; `null` for MCQ |

---

## 7. `POST /v1/bots/fun-fact`

Generates one short, real, age-appropriate fun fact in Persian based on the child's interests.

### Request

```json
{
  "interests": ["گربه", "فضا", "رنگ‌ها"]
}
```

### Optional request fields

| Field | Type | Description |
|-------|------|-------------|
| `user_prompt` | string | Extra generation instructions |
| `model` | string | Upstream model id |
| `max_output_tokens` | int | Token cap |

### Response `200`

```json
{
  "fact": "می‌دانستی گربه‌ها می‌توانند بیش از ۲۰ نوع صدا دربیاورند؟",
  "related_interest": "گربه",
  "interests": ["گربه", "فضا", "رنگ‌ها"],
  "model": "deepseek-v4-flash"
}
```

**Legacy alias:** `POST /v1/fun-fact` — same request/response body.

---

## 8. `POST /v1/chat/completions` (legacy)

OpenAI-compatible shape. Uses the **teacher** persona. Prefer `POST /v1/bots/teacher/chat` for new integrations.

### Request

```json
{
  "model": "deepseek-v4-flash",
  "messages": [
    { "role": "user", "content": "سلام!" }
  ]
}
```

Client `system` messages are ignored.

### Response `200`

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1756387200,
  "model": "deepseek-v4-flash",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "سلام! امروز چه چیزی یاد می‌گیریم؟"
      },
      "finish_reason": "stop"
    }
  ]
}
```

---

## Error responses

| Status | When |
|--------|------|
| `422` | Invalid request body (e.g. MCQ assess without `selected_option_ids`) |
| `404` | Unknown `bot_id` |
| `502` | Upstream AI error or unparseable model output |
| `503` | `AVALAI_API_KEY` not configured on server |

**Example `422`**

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body"],
      "msg": "Value error, selected_option_ids is required for assess_mode=mcq",
      "input": {}
    }
  ]
}
```

**Example `502`**

```json
{
  "detail": "Assessment parse failed: model did not return JSON"
}
```

---

## Integration checklist (Laravel / backend)

1. On app start, call `GET /v1/contracts` and cache question types + `recommended_bot`.
2. For **chat**, persist `history` in your DB; send `message` + `history` on each turn.
3. For **assess**, send `question_type_id` + either `selected_option_ids` (MCQ) or `answer` (open).
4. For **generate**, store `exercises[]` items using the contract shape (`story_page` + `exercise`).
5. Never expose `AVALAI_API_KEY` to the client — only your backend calls this API.
