import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()

class EsqueciMinhaSenhaSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, min_length=7, max_length=8)
