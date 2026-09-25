from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import require
from common.rbac import USE_AI_ASSISTANT

from .services import analyze_weak_topics, ask_ai_assistant


class AskSerializer(serializers.Serializer):
    question = serializers.CharField()
    subject = serializers.IntegerField(required=False)


class WeakTopicSerializer(serializers.Serializer):
    subject = serializers.IntegerField()
    subject_name = serializers.CharField()
    average = serializers.FloatField()


class AIAskView(APIView):
    permission_classes = [require(USE_AI_ASSISTANT)]
    serializer_class = AskSerializer

    def post(self, request):
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        subject_name = ""
        subject_id = serializer.validated_data.get("subject")
        if subject_id:
            from apps.subjects.models import Subject

            subject = get_object_or_404(Subject, pk=subject_id)
            subject_name = subject.name

        answer = ask_ai_assistant(serializer.validated_data["question"], subject_name)
        return Response({"success": True, "answer": answer})


class WeakTopicsView(APIView):
    permission_classes = [require(USE_AI_ASSISTANT)]
    serializer_class = WeakTopicSerializer

    def get(self, request):
        from apps.users.models import StudentProfile

        student = get_object_or_404(StudentProfile, user=request.user)
        weak_topics = analyze_weak_topics(student)
        return Response({"success": True, "weak_topics": weak_topics})
