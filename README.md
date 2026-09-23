# MaktabIQ

Zamonaviy maktab boshqaruv va ta'lim platformasi — Django + DRF backend va React + Vite
frontend.

- **Backend:** `/` (shu papka) — quyida hujjatlashtirilgan
- **Frontend:** [`frontend/`](frontend/README.md) — React + Vite + Tailwind, barcha 5 rol
  (SUPERADMIN/ADMIN/TEACHER/STUDENT/PARENT) uchun moslashuvchan UI
- **Telegram Mini App:** [`telegram-app/`](telegram-app/README.md) — Telegram ichida ochiladigan
  yengil ilova (parolsiz kirish, bugungi darslar/baholar/bildirishnomalar)

## Backend

## Stack

- Django 5 + Django REST Framework
- PostgreSQL
- JWT auth (djangorestframework-simplejwt)
- Django Channels + Redis (real-time chat, notifications)
- Celery + Redis (background tasks: absent notification, telegram, weekly report)
- drf-spectacular (Swagger / OpenAPI)
- Telegram Bot (python-telegram-bot)

## Loyiha tuzilishi

```
maktabiq/
    config/           # settings, urls, asgi, wsgi, celery
    apps/
        users/        # User, StudentProfile, TeacherProfile, ParentProfile,
                       # transfer history, documents, health records, auth
        schools/
        classes/      # ClassRoom, AcademicYear, Quarter
        subjects/
        lessons/      # dars jadvali + conflict tekshiruvi
        assignments/  # Homework + Submission
        grades/       # Baholar + choraklik/yillik hisob-kitob
        attendance/   # Student/Teacher attendance
        notifications/# Notification, Announcement, Emergency + Celery tasks
        chat/         # Real-time chat (Channels)
        analytics/    # StudentProgress, admin statistikasi
        library/      # Digital library
        quizzes/      # Quiz / Question / QuizAttempt
        helpdesk/     # HelpDeskTicket
        ai/           # AI Study Assistant
    common/           # base model, pagination, permissions, exception handler,
                       # audit log, JWT websocket auth, telegram helper
    bot/              # Telegram bot (polling)
```

## O'rnatish (local)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

copy .env.example .env        # kerakli qiymatlarni to'ldiring
```

PostgreSQL va Redis ishga tushirilgan bo'lishi kerak (yoki `docker compose up db redis`).

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- REST API: http://localhost:8000/api/v1/
- Swagger: http://localhost:8000/api/docs/
- Admin: http://localhost:8000/admin/

Real-time (Channels) uchun ASGI server kerak:

```bash
daphne -b 0.0.0.0 -p 8001 config.asgi:application
```

Celery worker/beat:

```bash
celery -A config worker -l info
celery -A config beat -l info
```

Telegram bot:

```bash
python -m bot.bot
```

## Docker

```bash
docker compose up --build
```

## Testlar

```bash
python manage.py test --settings=config.settings.test
```

## Rollar

`SUPERADMIN`, `ADMIN`, `TEACHER`, `STUDENT`, `PARENT` — barcha permissionlar backend
tomonidan (`common/permissions.py` va har bir app'ning `permissions.py`) tekshiriladi.

## Muhim endpointlar

Barcha endpointlar `/api/v1/` ostida (to'liq ro'yxat uchun Swagger'ga qarang):

- `POST /api/v1/auth/login/`, `/refresh/`, `/logout/`
- `POST /api/v1/auth/telegram/` — Telegram Mini App uchun parolsiz kirish (initData orqali)
- `POST /api/v1/auth/telegram/login/` — Mini App'da birinchi marta bog'lash (initData + parol)
- `POST /api/v1/auth/register/student/`
- `GET /api/v1/students/?search=Az`
- `POST /api/v1/students/{id}/transfer/`
- `GET /api/v1/grades/annual/?student=&academic_year=`
- `GET /api/v1/attendance/calendar/?student=&month=&year=`
- `PATCH /api/v1/attendance/{id}/submit_reason/`
- `POST /api/v1/assignments/{id}/submit/`
- `POST /api/v1/submissions/{id}/grade/`
- `POST /api/v1/quizzes/{id}/submit/`
- `GET /api/v1/analytics/progress/`, `/api/v1/analytics/admin/`
- `GET /api/v1/ai/weak-topics/`, `POST /api/v1/ai/ask/`
- `ws://.../ws/notifications/?token=<access>`
- `ws://.../ws/chat/<room_id>/?token=<access>`

## Hozircha to'liq emas / keyingi bosqich

- AI provider bilan real integratsiya (hozircha `AI_PROVIDER_API_KEY` bo'lmasa fallback javob qaytaradi)
- Telegram bot — real webhook deploy (hozircha polling skeleti)
- To'liq test qamrovi (asosiy permission/business-rule testlari yozilgan, ammo har bir endpoint uchun emas)
