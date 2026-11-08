from django.urls import path

from .views import LoginView, LogoutView, MeView

app_name = "accounts"

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
]
