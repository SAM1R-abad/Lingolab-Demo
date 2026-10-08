from django.urls import path

from .views import (
    CefrLevelsView,
    QuestionDetailView,
    QuestionListCreateView,
    SessionListView,
    SessionResultView,
    SessionStatusView,
    StartSessionView,
    SubmitAnswerView,
)

app_name = "assessment"

urlpatterns = [
    path("levels/", CefrLevelsView.as_view(), name="levels"),
    path("sessions/", SessionListView.as_view(), name="sessions"),
    path("questions/", QuestionListCreateView.as_view(), name="questions"),
    path("questions/<int:pk>/", QuestionDetailView.as_view(), name="question-detail"),
    path("start/", StartSessionView.as_view(), name="start"),
    path("<int:session_id>/", SessionStatusView.as_view(), name="status"),
    path("<int:session_id>/answer/", SubmitAnswerView.as_view(), name="answer"),
    path("<int:session_id>/result/", SessionResultView.as_view(), name="result"),
]
