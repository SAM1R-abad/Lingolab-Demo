from django.urls import path

from .views import AdminUserDetailView, AdminUserListView, GuestLoginView, LoginView, MeView, SignUpView

app_name = "accounts"

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("guest/", GuestLoginView.as_view(), name="guest"),
    path("me/", MeView.as_view(), name="me"),
    path("users/", AdminUserListView.as_view(), name="user-list"),
    path("users/<int:pk>/", AdminUserDetailView.as_view(), name="user-detail"),
]
