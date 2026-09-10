# Serendipity Chatbot API — Sample Requests

Base URLs:

| Environment | URL |
|-------------|-----|
| Local | `http://127.0.0.1:8001` |
| VPS (SSH / Laravel) | `http://127.0.0.1:8001` |
| From Mac via tunnel | `http://localhost:8001` after `ssh -L 8001:127.0.0.1:8001 root@89.44.241.36` |

All POST requests use header: `Content-Type: application/json`

Swagger UI: `/docs`

---

## 1. Health

```bash
curl -s http://127.0.0.1:8001/health
```

Response:

```json
{ "status": "ok" }
```

---

## 2. Contracts (exercise schemas)

```bash
curl -s http://127.0.0.1:8001/v1/contracts | python3 -m json.tool
```

---

## 3. List bots

```bash
curl -s http://127.0.0.1:8001/v1/bots | python3 -m json.tool
```

Returns: `teacher`, `story`, `assess`, `generate`, `fun-fact`

---

## 4. Teacher chat (open / divergent help)

### Turn 1 — no history

```bash
curl -s http://127.0.0.1:8001/v1/bots/teacher/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "اگر من یک ربات داشتم از او می‌خواستم اسباب‌بازی‌هایم را جمع کند.",
    "history": []
  }' | python3 -m json.tool
```

### Turn 2 — with history (memory test)

Replace `PASTE_REPLY` with the assistant reply from turn 1.

```bash
curl -s http://127.0.0.1:8001/v1/bots/teacher/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "می‌تونی جمله‌ام را کامل‌تر کنی؟",
    "history": [
      {
        "role": "user",
        "content": "اگر من یک ربات داشتم از او می‌خواستم اسباب‌بازی‌هایم را جمع کند."
      },
      {
        "role": "assistant",
        "content": "PASTE_REPLY"
      }
    ]
  }' | python3 -m json.tool
```

### With story context (user_prompt)

```bash
curl -s http://127.0.0.1:8001/v1/bots/teacher/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "سلام! این داستان درباره چیه؟",
    "history": [],
    "user_prompt": "متن داستان: سام یک نامه پیدا کرد و کنجکاو شد بداند فرستنده کیست."
  }' | python3 -m json.tool
```

Expected response shape:

```json
{
  "bot_id": "teacher",
  "reply": "...",
  "model": "gpt-5.6-luna",
  "history_turns_used": 0
}
```

---

## 5. Story chat (story / convergent hints)

```bash
curl -s http://127.0.0.1:8001/v1/bots/story/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "به نظرت سام بیشتر دوست داشت درباره کدام قسمت نامه بداند؟",
    "history": [],
    "user_prompt": "متن داستان: سام نامه‌ای در جعبه قدیمی پیدا کرد."
  }' | python3 -m json.tool
```

---

## 6. Assess — divergent (open_question)

```bash
curl -s http://127.0.0.1:8001/v1/bots/assess \
  -H "Content-Type: application/json" \
  -d '{
    "question_type_id": "open_question",
    "question": "اگر جای سام بودی چه کاری انجام می‌دادی؟",
    "answer": "نامه را می‌خواندم و به دوستم زنگ می‌زدم.",
    "interests": ["دوستان", "داستان"],
    "areas": [
      {
        "name": "فارسی",
        "sub_areas": [
          {
            "name": "ساخت جمله",
            "objectives": [
              "ساخت جمله‌های کامل و درست با حداقل ۷ واژه"
            ]
          }
        ]
      }
    ]
  }' | python3 -m json.tool
```

Expected response:

```json
{
  "question_mode": "divergent",
  "question_type_id": "open_question",
  "assess_mode": "open",
  "assessments": [
    {
      "area": "فارسی",
      "sub_area": "ساخت جمله",
      "objective": "...",
      "status": "partial",
      "score": 3,
      "feedback": "..."
    }
  ],
  "overall_score": 3,
  "score_segment": "توانمند",
  "summary": "..."
}
```

---

## 7. Assess — convergent (mcq_single)

```bash
curl -s http://127.0.0.1:8001/v1/bots/assess \
  -H "Content-Type: application/json" \
  -d '{
    "question_type_id": "mcq_single",
    "question": "کدام احساس‌ها با رفتار شخصیت داستان هماهنگ هستند؟",
    "selected_option_ids": ["curious", "excited"],
    "correct_option_ids": ["curious", "excited"],
    "options": [
      { "id": "curious", "label": "کنجکاو" },
      { "id": "excited", "label": "هیجان‌زده" },
      { "id": "afraid", "label": "ترسیده" },
      { "id": "angry", "label": "عصبانی" }
    ],
    "interests": ["داستان"],
    "areas": [
      {
        "name": "دیگرآگاهی هیجانی",
        "sub_areas": [
          {
            "name": "درک احساس",
            "objectives": ["احساس شخصیت را درست تشخیص دهد"]
          }
        ]
      }
    ]
  }' | python3 -m json.tool
```

---

## 8. Assess — convergent (mcq_multi)

```bash
curl -s http://127.0.0.1:8001/v1/bots/assess \
  -H "Content-Type: application/json" \
  -d '{
    "question_type_id": "mcq_multi",
    "question": "کدام موضوعات در نامه مطرح شده بود؟",
    "selected_option_ids": ["topic-1", "topic-3"],
    "correct_option_ids": ["topic-1", "topic-2", "topic-3"],
    "options": [
      { "id": "topic-1", "label": "سفر" },
      { "id": "topic-2", "label": "دوستی" },
      { "id": "topic-3", "label": "کتاب" },
      { "id": "topic-4", "label": "ورزش" }
    ],
    "areas": [
      {
        "name": "فارسی",
        "sub_areas": [
          {
            "name": "درک مطلب",
            "objectives": ["موضوعات اصلی متن را تشخیص دهد"]
          }
        ]
      }
    ]
  }' | python3 -m json.tool
```

---

## 9. Assess — convergent (image_mcq)

```bash
curl -s http://127.0.0.1:8001/v1/bots/assess \
  -H "Content-Type: application/json" \
  -d '{
    "question_type_id": "image_mcq",
    "question": "سه تصویر مرتبط با داستان را انتخاب کن.",
    "selected_option_ids": ["image-1", "image-2", "image-3"],
    "correct_option_ids": ["image-1", "image-2", "image-3"],
    "options": [
      { "id": "image-1", "alt": "نامه قدیمی", "image_path": "images/image-1.png" },
      { "id": "image-2", "alt": "جعبه چوبی", "image_path": "images/image-2.png" },
      { "id": "image-3", "alt": "پسر کنجکاو", "image_path": "images/image-3.png" },
      { "id": "image-4", "alt": "توپ فوتبال", "image_path": "images/image-4.png" }
    ],
    "areas": [
      {
        "name": "فارسی",
        "sub_areas": [
          {
            "name": "درک تصویری",
            "objectives": ["تصاویر مرتبط با داستان را انتخاب کند"]
          }
        ]
      }
    ]
  }' | python3 -m json.tool
```

---

## 10. Generate exercises — divergent

```bash
curl -s http://127.0.0.1:8001/v1/bots/generate-exercises \
  -H "Content-Type: application/json" \
  -d '{
    "question_type_id": "open_question",
    "question": "اگر جای سام بودی چه کاری انجام می‌دادی؟",
    "answer": "نامه را می‌خواندم و با دوستانم درباره‌اش صحبت می‌کردم.",
    "interests": ["دوستان", "داستان"],
    "count": 3
  }' | python3 -m json.tool
```

---

## 11. Generate exercises — convergent (mcq_single)

```bash
curl -s http://127.0.0.1:8001/v1/bots/generate-exercises \
  -H "Content-Type: application/json" \
  -d '{
    "question_type_id": "mcq_single",
    "question": "سام در نامه بیشتر درباره چه چیزی کنجکاو بود؟",
    "answer": "درباره اینکه چه کسی نامه را فرستاده",
    "interests": ["کنجکاوی"],
    "count": 2
  }' | python3 -m json.tool
```

---

## 12. Fun fact

```bash
curl -s http://127.0.0.1:8001/v1/bots/fun-fact \
  -H "Content-Type: application/json" \
  -d '{
    "interests": ["ربات", "فضا"]
  }' | python3 -m json.tool
```

Expected response:

```json
{
  "fact": "...",
  "related_interest": "ربات",
  "interests": ["ربات", "فضا"],
  "model": "gpt-5.6-luna"
}
```

---

## 13. Chat history — 3-turn flow (Laravel pattern)

**Turn 1**

```json
{ "message": "اسم من سام است و ربات دوست دارم.", "history": [] }
```

**Turn 2** — save turn 1 user + assistant to DB, send as history:

```json
{
  "message": "چه کارهایی از ربات می‌خواستم انجام بده؟",
  "history": [
    { "role": "user", "content": "اسم من سام است و ربات دوست دارم." },
    { "role": "assistant", "content": "...reply from turn 1..." }
  ]
}
```

**Turn 3**

```json
{
  "message": "اسم من چی بود؟",
  "history": [
    { "role": "user", "content": "اسم من سام است و ربات دوست دارم." },
    { "role": "assistant", "content": "...turn 1 reply..." },
    { "role": "user", "content": "چه کارهایی از ربات می‌خواستم انجام بده؟" },
    { "role": "assistant", "content": "...turn 2 reply..." }
  ]
}
```

Zal should remember **سام** and **ربات** on turn 3.

---

## 14. Legacy endpoints (still work)

```bash
# OpenAI-shaped chat (teacher persona)
curl -s http://127.0.0.1:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{ "role": "user", "content": "سلام!" }]
  }' | python3 -m json.tool

# Assess alias
curl -s http://127.0.0.1:8001/v1/assess \
  -H "Content-Type: application/json" \
  -d '{ ... same body as /v1/bots/assess ... }'

# Fun fact alias
curl -s http://127.0.0.1:8001/v1/fun-fact \
  -H "Content-Type: application/json" \
  -d '{ "interests": ["گربه"] }' | python3 -m json.tool
```

---

## 15. Swagger (Try it out)

1. Start server: `uvicorn app.main:app --reload --host 127.0.0.1 --port 8001`
2. Open: http://127.0.0.1:8001/docs
3. Expand endpoint → **Try it out** → paste JSON → **Execute**

---

## Quick reference

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Health check |
| `GET /v1/contracts` | Exercise schemas |
| `GET /v1/bots` | List services |
| `POST /v1/bots/teacher/chat` | Educational chat |
| `POST /v1/bots/story/chat` | Story chat |
| `POST /v1/bots/assess` | Score answer |
| `POST /v1/bots/generate-exercises` | Similar exercises |
| `POST /v1/bots/fun-fact` | Fun fact from interests |

See also: `docs/backend-chatbot-api-v2.html`
