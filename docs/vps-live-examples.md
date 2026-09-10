# Serendipity API — نمونه‌های واقعی از VPS

> تست‌شده روی سرور: `http://127.0.0.1:8001` · تاریخ: ۲۸ اوت ۲۰۲۶  
> مدل: `gpt-5.6-luna` · سرویس: `serendipity-api`

این سند از **ورودی/خروجی واقعی** ترمینال VPS ساخته شده (curl).

---

## 1. Health

**Request**
```bash
curl http://127.0.0.1:8001/health
```

**Response `200`**
```json
{ "status": "ok" }
```

---

## 2. Contracts

**Request**
```bash
curl http://127.0.0.1:8001/v1/contracts
```

**Response `200`** (خلاصه)
```json
{
  "schema_version": "1.1",
  "question_modes": {
    "convergent": {
      "label_fa": "همگرا",
      "layouts": ["multiple_choice", "image_multiple_choice"]
    },
    "divergent": {
      "label_fa": "واگرا",
      "layouts": ["question"]
    }
  },
  "question_types": [
    { "id": "mcq_single", "question_mode": "convergent", "assess_mode": "mcq", "recommended_bot": "story" },
    { "id": "mcq_multi", "question_mode": "convergent", "assess_mode": "mcq", "recommended_bot": "story" },
    { "id": "open_question", "question_mode": "divergent", "assess_mode": "open", "recommended_bot": "teacher" },
    { "id": "image_mcq", "question_mode": "convergent", "assess_mode": "mcq", "recommended_bot": "story" }
  ],
  "examples": [ "... see GET /v1/contracts for full payload ..." ]
}
```

---

## 3. List bots

**Request**
```bash
curl http://127.0.0.1:8001/v1/bots
```

**Response `200`**
```json
[
  {
    "id": "teacher",
    "name": "زال",
    "description": "همراه مهربان — کمک در پاسخ تشریحی، جمله‌سازی، و گفتگوی آموزشی",
    "chat_url": "/v1/bots/teacher/chat"
  },
  {
    "id": "story",
    "name": "زال — داستان",
    "description": "کمک در درک داستان، احساس شخصیت‌ها، نشانه‌ها، و سؤال‌های مرتبط با متن",
    "chat_url": "/v1/bots/story/chat"
  },
  {
    "id": "assess",
    "name": "ارزیاب پاسخ",
    "assess_url": "/v1/bots/assess"
  },
  {
    "id": "generate",
    "name": "تولید تمرین",
    "generate_url": "/v1/bots/generate-exercises"
  },
  {
    "id": "fun-fact",
    "name": "حقیقت جالب",
    "fun_fact_url": "/v1/bots/fun-fact"
  }
]
```

---

## 4. Teacher chat — دور ۱

**Request**
```bash
curl -s http://127.0.0.1:8001/v1/bots/teacher/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"سلام! اسم من سام است.","history":[]}'
```

**Response `200`**
```json
{
  "bot_id": "teacher",
  "reply": "سلام سام جان! روزت بخیر و شادی. 🌸\n\nخیلی خوشحالم که با من صحبت می‌کنی. اسم قشنگی داری!\nسام عزیز، امروز چطور می‌توانی به من کمک کنی؟ دوست داری با هم درباره‌ی درس‌های مدرسه حرف بزنیم، یک داستان قشنگ بخوانیم یا یک معمای باحال حل کنیم؟\n\nهر چه که دوست داری را به من بگو، من سراپا گوشم! 😊✏️",
  "model": "gpt-5.6-luna",
  "history_turns_used": 0
}
```

---

## 5. Teacher chat — دور ۲ (تست history)

**Request** — `PASTE_REPLY_FROM_TURN_1` را با `reply` واقعی دور ۱ عوض کنید.

```bash
curl -s http://127.0.0.1:8001/v1/bots/teacher/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "اسم من چی بود؟",
    "history": [
      { "role": "user", "content": "سلام! اسم من سام است." },
      { "role": "assistant", "content": "PASTE_REPLY_FROM_TURN_1" }
    ]
  }'
```

**Response `200`** (با placeholder هم کار کرد — مدل از history.user «سام» را فهمید)
```json
{
  "bot_id": "teacher",
  "reply": "سلام سام جان! اسم قشنگت سام است.\n\nیادت رفته بود، عزیز دلم؟ اشکالی ندارد، آدم گاهی فراموش می‌کند! ...",
  "model": "gpt-5.6-luna",
  "history_turns_used": 1
}
```

---

## 6. Story chat

**Request** — `user_prompt` باید **متن واقعی داستان** باشد، نه `...`

```bash
curl -s http://127.0.0.1:8001/v1/bots/story/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "سام درباره چی کنجکاو بود؟",
    "history": [],
    "user_prompt": "متن داستان: سام در اتاق قدیمی خانه یک نامه پیدا کرد. او کنجکاو شد بداند چه کسی نامه را فرستاده."
  }'
```

**Response `200`** (وقتی `user_prompt` فقط `متن داستان: ...` بود)
```json
{
  "bot_id": "story",
  "reply": "سلام دوست قشنگم!\n\nآفرین که با دقت به داستان گوش دادی. اما گفتی «متن داستان: ...»، یعنی هنوز داستان را برای من نفرستادی! ...",
  "model": "gpt-5.6-luna",
  "history_turns_used": 0
}
```

---

## 7. Assess — واگرا (open_question) ✅

**Request**
```bash
curl -s http://127.0.0.1:8001/v1/bots/assess \
  -H "Content-Type: application/json" \
  -d '{
    "question_type_id": "open_question",
    "question": "اگر جای سام بودی چه می‌کردی؟",
    "answer": "نامه را می‌خواندم.",
    "interests": ["داستان"],
    "areas": [{
      "name": "فارسی",
      "sub_areas": [{
        "name": "ساخت جمله",
        "objectives": ["جمله کامل"]
      }]
    }]
  }'
```

**Response `200`**
```json
{
  "question_mode": "divergent",
  "question_type_id": "open_question",
  "assess_mode": "open",
  "assessments": [
    {
      "area": "فارسی",
      "sub_area": "ساخت جمله",
      "objective": "جمله کامل",
      "status": "met",
      "score": 5,
      "feedback": "آفرین که پاسخت یک جمله کامل و با‌معنی بود! انگار خودت را خوب جای سام گذاشتی و دوست داری داستان را دنبال کنی."
    }
  ],
  "overall_score": 5,
  "score_segment": "پیشرو",
  "summary": "پاسخ کودک کامل و مرتبط با داستان بود و objective را برآورده کرده است."
}
```

---

## 8. Assess — همگرا (mcq_single) ✅

**Request**
```bash
curl -s http://127.0.0.1:8001/v1/bots/assess \
  -H "Content-Type: application/json" \
  -d '{
    "question_type_id": "mcq_single",
    "question": "کدام احساس درست است؟",
    "selected_option_ids": ["curious"],
    "correct_option_ids": ["curious"],
    "options": [
      { "id": "curious", "label": "کنجکاو" },
      { "id": "afraid", "label": "ترسیده" }
    ],
    "areas": [{
      "name": "هیجان",
      "sub_areas": [{
        "name": "درک",
        "objectives": ["احساس درست"]
      }]
    }]
  }'
```

**Response `200`**
```json
{
  "question_mode": "convergent",
  "question_type_id": "mcq_single",
  "assess_mode": "mcq",
  "assessments": [
    {
      "area": "هیجان",
      "sub_area": "درک",
      "objective": "احساس درست",
      "status": "met",
      "score": 5,
      "feedback": "آفرین! گزینهٔ درست را به خوبی تشخیص دادی و احساس کنجکاوی را به درست انتخاب کردی."
    }
  ],
  "overall_score": 5,
  "score_segment": "پیشرو",
  "summary": "دانش‌آموز پاسخ صحیح را انتخاب کرد."
}
```

**نکته:** اولین بار `rate_limit_exceeded` از AvalAI آمد — چند ثانیه صبر کنید و دوباره بزنید.

---

## 9. Generate exercises ✅

**Request**
```bash
curl -s http://127.0.0.1:8001/v1/bots/generate-exercises \
  -H "Content-Type: application/json" \
  -d '{
    "question_type_id": "open_question",
    "question": "اگر جای سام بودی چه می‌کردی؟",
    "answer": "نامه را می‌خواندم.",
    "count": 3
  }'
```

**Response `200`** (نمونه — هر بار سؤال‌های متفاوت)
```json
{
  "schema_version": "1.1",
  "source_question": "اگر جای سام بودی چه می‌کردی؟",
  "question_type_id": "open_question",
  "question_mode": "divergent",
  "exercises": [
    {
      "question_type_id": "open_question",
      "story_page": {
        "type": "exercise",
        "title": "سؤال خلاقانه",
        "text": "اگر به جای سارا بودی، چه هدیه‌ای برای دوستت می‌ساختی؟",
        "meta": {
          "layout": "question",
          "question_mode": "divergent",
          "max_words_per_answer": 120,
          "answer_placeholders": ["پاسخت را اینجا بنویس..."]
        }
      },
      "exercise": null,
      "sample_answer": "یک نقاشی قشنگ از طبیعت می‌کشیدم."
    },
    {
      "question_type_id": "open_question",
      "story_page": {
        "title": "سؤال خلاقانه",
        "text": "اگر یک روز پرنده بودی، دوست داشتی کجا پرواز کنی؟"
      },
      "sample_answer": "دوست داشتم بالای کوه‌های بلند و جنگل‌های سرسبز پرواز کنم."
    },
    {
      "question_type_id": "open_question",
      "story_page": {
        "title": "سؤال خلاقانه",
        "text": "اگر در باغچه‌تان یک بذر جادویی پیدا می‌کردی، چه انتظاری داشتی از آن رشد کند؟"
      },
      "sample_answer": "دوست داشتم درختی رشد کند که به جای میوه، اسباب‌بازی‌های رنگارنگ داشته باشد."
    }
  ],
  "model": "gpt-5.6-luna"
}
```

---

## 10. Fun fact ✅

**Request**
```bash
curl -s http://127.0.0.1:8001/v1/bots/fun-fact \
  -H "Content-Type: application/json" \
  -d '{"interests":["ربات","فضا"]}'
```

**Response `200`**
```json
{
  "fact": "در مریخ یک ربات کاوشگر شجاع به اسم «پشتکار» داریم که مثل یک دانشمند کوچک دارد خاک‌ها را بو می‌کند و عکس می‌فرستد!",
  "related_interest": "ربات",
  "interests": ["ربات", "فضا"],
  "model": "gpt-5.6-luna"
}
```

---

## خطاهای مشاهده‌شده در تست

### Rate limit (AvalAI)
```json
{
  "detail": {
    "error": {
      "code": "rate_limit_exceeded",
      "message": "Rate limit reached for requests..."
    }
  }
}
```
**راه‌حل:** بین درخواست‌ها ۵–۱۰ ثانیه فاصله بگذارید. جزئیات: https://ava.al/limits

### JSON invalid (دو curl پشت سر هم)
```json
{
  "detail": [{
    "type": "json_invalid",
    "msg": "JSON decode error",
    "ctx": { "error": "Extra data" }
  }]
}
```
**راه‌حل:** هر curl را **جدا** اجرا کنید — دو دستور را به هم نچسبانید.

---

## جمع‌بندی تست VPS

| Endpoint | وضعیت |
|----------|--------|
| `GET /health` | ✅ |
| `GET /v1/contracts` | ✅ |
| `GET /v1/bots` | ✅ |
| `POST /v1/bots/teacher/chat` | ✅ |
| `POST /v1/bots/teacher/chat` + history | ✅ |
| `POST /v1/bots/story/chat` | ✅ (نیاز به متن واقعی داستان در `user_prompt`) |
| `POST /v1/bots/assess` open | ✅ |
| `POST /v1/bots/assess` mcq | ✅ (بعد از rate limit) |
| `POST /v1/bots/generate-exercises` | ✅ |
| `POST /v1/bots/fun-fact` | ✅ |

---

## Laravel

```env
CHATBOT_API_URL=http://127.0.0.1:8001
```

مرجع کامل: `docs/backend-chatbot-api-v2.html` · نمونه curl: `docs/sample-requests.md`
