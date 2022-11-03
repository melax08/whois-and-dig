from rest_framework import serializers


class WhoisSerializer(serializers.Serializer):
    domain = serializers.CharField(max_length=256)


class DigSerializer(serializers.Serializer):
    ...
