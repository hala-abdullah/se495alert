from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )


class IdentitySerializer(serializers.Serializer):
    """Read-only shape of the identity payload (documentation + tests)."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    display_name = serializers.CharField()
    student_id = serializers.CharField(allow_null=True)
    role_family = serializers.CharField()
    campus_role = serializers.CharField()
    system_role = serializers.CharField()
    permissions = serializers.DictField()
