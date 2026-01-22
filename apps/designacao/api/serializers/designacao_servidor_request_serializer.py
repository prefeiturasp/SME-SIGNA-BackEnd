from rest_framework import serializers


class DesignacaoServidorRequestSerializer(serializers.Serializer):
    rf = serializers.CharField()
