import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Siz MaktabIQ platformasidagi AI Study Assistant'siz. Maqsadingiz o'quvchiga "
    "mavzuni tushuntirish, misollar va mashqlar berish, xatolarini tushuntirish. "
    "Javoblaringiz qisqa, aniq va o'quvchi darajasiga mos bo'lsin."
)


def ask_ai_assistant(question: str, subject_name: str = "") -> str:
    if not settings.AI_PROVIDER_API_KEY:
        return (
            "AI Study Assistant hozircha sozlanmagan (AI_PROVIDER_API_KEY yo'q). "
            f"Savolingiz qabul qilindi: \"{question}\""
        )

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.AI_PROVIDER_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-5",
                "max_tokens": 512,
                "system": SYSTEM_PROMPT,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Fan: {subject_name or 'umumiy'}\nSavol: {question}",
                    }
                ],
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return "".join(block.get("text", "") for block in data.get("content", []))
    except requests.RequestException:
        logger.exception("AI provider request failed")
        return "AI Assistant hozircha javob bera olmadi. Birozdan so'ng qayta urinib ko'ring."


def analyze_weak_topics(student):
    from django.db.models import Avg

    from apps.grades.models import Grade

    weak_subjects = (
        Grade.objects.filter(student=student)
        .values("subject_id", "subject__name")
        .annotate(average=Avg("value"))
        .filter(average__lt=6)
        .order_by("average")
    )
    return [
        {"subject": row["subject_id"], "subject_name": row["subject__name"], "average": round(row["average"], 2)}
        for row in weak_subjects
    ]
