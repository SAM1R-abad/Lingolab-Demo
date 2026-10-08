from rest_framework import serializers

from .models import PlacementSession, Question, SessionQuestion, Skill


class QuestionAdminSerializer(serializers.ModelSerializer):
    """
    Full Question representation for admin CRUD (includes `correct_answer`,
    unlike QuestionPublicSerializer which is what test-takers ever see).
    """

    class Meta:
        model = Question
        fields = (
            "id",
            "external_id",
            "skill",
            "level",
            "question_type",
            "prompt",
            "options",
            "correct_answer",
            "tag",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_options(self, value):
        if not isinstance(value, list) or len(value) != 4:
            raise serializers.ValidationError("`options` must be a list of exactly 4 strings.")
        if not all(isinstance(o, str) and o.strip() for o in value):
            raise serializers.ValidationError("Every option must be a non-empty string.")
        if len(set(value)) != len(value):
            raise serializers.ValidationError("Options must be unique.")
        return value

    def validate(self, attrs):
        options = attrs.get("options", getattr(self.instance, "options", None))
        correct_answer = attrs.get("correct_answer", getattr(self.instance, "correct_answer", None))
        if options is not None and correct_answer is not None and correct_answer not in options:
            raise serializers.ValidationError(
                {"correct_answer": "`correct_answer` must be an exact copy of one of the `options`."}
            )
        return attrs


class StartSessionSerializer(serializers.Serializer):
    skill = serializers.ChoiceField(choices=Skill.choices)


class SubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    answer = serializers.CharField()

    def validate(self, attrs):
        try:
            question = Question.objects.get(id=attrs["question_id"])
        except Question.DoesNotExist:
            raise serializers.ValidationError({"question_id": "No question with this id exists."})
        if attrs["answer"] not in question.options:
            raise serializers.ValidationError(
                {"answer": "This answer is not one of the question's options."}
            )
        return attrs


class QuestionPublicSerializer(serializers.ModelSerializer):
    """Question representation shown to the test-taker: never includes `correct_answer`."""

    class Meta:
        model = Question
        fields = ("id", "level", "question_type", "prompt", "options", "tag")


class SessionQuestionSerializer(serializers.ModelSerializer):
    question = QuestionPublicSerializer()

    class Meta:
        model = SessionQuestion
        fields = ("id", "order", "level", "question", "selected_answer", "is_correct", "answered_at")


class PlacementSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlacementSession
        fields = (
            "id",
            "skill",
            "status",
            "current_level",
            "passed_levels",
            "result_level",
            "created_at",
            "updated_at",
            "completed_at",
        )
        read_only_fields = fields


class SessionResultSerializer(serializers.ModelSerializer):
    level_breakdown = serializers.SerializerMethodField()

    class Meta:
        model = PlacementSession
        fields = (
            "id",
            "skill",
            "status",
            "result_level",
            "passed_levels",
            "level_breakdown",
            "completed_at",
        )

    def get_level_breakdown(self, obj):
        # Populated by the view from AdaptiveEngine.level_breakdown()
        return self.context.get("level_breakdown", [])
