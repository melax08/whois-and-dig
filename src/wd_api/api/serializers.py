from rest_framework import serializers


class WhoisSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=256)


class DigSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=256)
    record = serializers.CharField(max_length=10, required=False)
    dns = serializers.ListField(required=False)


class DigSettingsSerializer(serializers.Serializer):
    default_type = serializers.CharField(max_length=10)
    allowed_records = serializers.ListField()
