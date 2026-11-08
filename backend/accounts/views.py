"""Authentication endpoints (US-9, AC-9.1–9.5, NFR-21).

Login is the only endpoint in this app that accepts unauthenticated traffic.
Logout and identity require a valid token.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from audit.models import AuditLogEntry
from audit.writer import log

from .serializers import IdentitySerializer, LoginSerializer
from .services import authenticate_credentials, build_identity, get_profile


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate_credentials(username=username, password=password)
        if user is None:
            # One generic message whether the username or the password was
            # wrong (AC-9.1), and no hint about which accounts exist.
            log(
                action=AuditLogEntry.Action.LOGIN_FAILED,
                actor_label=username,
                object_type="auth",
                detail={"reason": "invalid_credentials"},
            )
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        profile = get_profile(user)
        token, _ = Token.objects.get_or_create(user=user)
        log(
            action=AuditLogEntry.Action.LOGIN_SUCCEEDED,
            actor=user,
            object_type="auth",
            detail={"role_family": profile.role_family},
        )
        return Response(
            {"token": token.key, "user": build_identity(user)},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    def post(self, request):
        Token.objects.filter(user=request.user).delete()
        log(
            action=AuditLogEntry.Action.LOGOUT,
            actor=request.user,
            object_type="auth",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    def get(self, request):
        data = build_identity(request.user)
        return Response(
            IdentitySerializer(instance=data).data,
            status=status.HTTP_200_OK,
        )
