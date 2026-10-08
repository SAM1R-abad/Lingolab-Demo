from django.urls import path

from apps.writing.views import (
    WritingSubmissionDetailView,
    WritingSubmissionListCreateView,
    WritingSubmissionResultView,
    WritingTaskAdminDetailView,
    WritingTaskAdminListCreateView,
    WritingTaskDetailView,
    WritingTaskListView,
)

app_name = "writing"

urlpatterns = [
    path("tasks/", WritingTaskListView.as_view(), name="task-list"),
    path("tasks/<int:pk>/", WritingTaskDetailView.as_view(), name="task-detail"),
    path("submissions/", WritingSubmissionListCreateView.as_view(), name="submission-list-create"),
    path("submissions/<int:submission_id>/", WritingSubmissionDetailView.as_view(), name="submission-detail"),
    path(
        "submissions/<int:submission_id>/result/",
        WritingSubmissionResultView.as_view(),
        name="submission-result",
    ),
    path("admin/tasks/", WritingTaskAdminListCreateView.as_view(), name="admin-task-list-create"),
    path("admin/tasks/<int:pk>/", WritingTaskAdminDetailView.as_view(), name="admin-task-detail"),
]
