from rest_framework import serializers

from .models import Question, Quiz, QuizAttempt


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ("id", "quiz", "question", "options", "correct_answer", "points")
        read_only_fields = ("id",)


class QuestionPublicSerializer(serializers.ModelSerializer):
    """Hides `correct_answer` from students taking the quiz."""

    class Meta:
        model = Question
        fields = ("id", "question", "options", "points")


class QuizSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    total_points = serializers.IntegerField(read_only=True)

    class Meta:
        model = Quiz
        fields = (
            "id",
            "title",
            "subject",
            "class_room",
            "teacher",
            "deadline",
            "time_limit_minutes",
            "questions",
            "total_points",
            "created_at",
        )
        read_only_fields = ("id", "teacher", "created_at")

    def get_questions(self, obj):
        from common import rbac

        request = self.context.get("request")
        # correct answers are only shown to people who manage or supervise quizzes
        privileged = bool(request) and rbac.has_any_perm(request.user, rbac.MANAGE_QUIZZES, rbac.VIEW_ALL_QUIZZES)
        serializer_cls = QuestionSerializer if privileged else QuestionPublicSerializer
        return serializer_cls(obj.questions.all(), many=True).data


class QuizAttemptSubmitSerializer(serializers.Serializer):
    answers = serializers.DictField(child=serializers.IntegerField())


class QuizAttemptSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.get_full_name", read_only=True)

    class Meta:
        model = QuizAttempt
        fields = (
            "id",
            "quiz",
            "student",
            "student_name",
            "answers",
            "score",
            "max_score",
            "started_at",
            "submitted_at",
        )
        read_only_fields = fields
