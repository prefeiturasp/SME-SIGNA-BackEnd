import logging
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str

logger = logging.getLogger(__name__)

User = get_user_model()

class EsqueciMinhaSenhaSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, min_length=7, max_length=8)

class RedefinirSenhaSerializer(serializers.Serializer):
    """
    Serializer para redefinição de senha usando UID com validações robustas.
    
    Campos:
    - uid: ID do usuário codificado em base64 (obrigatório)
    - token: Token de redefinição (obrigatório) 
    - password: Nova senha (obrigatório, mín. 8 caracteres)
    - password2: Confirmação da senha (obrigatório)
    """

    uid = serializers.CharField()
    token = serializers.CharField()
    new_pass = serializers.CharField(write_only=True, trim_whitespace=False)
    new_pass_confirm = serializers.CharField(write_only=True, trim_whitespace=False)

    default_error_messages = {
        "user_not_found": "Usuário não encontrado.",
        "token_invalid": "Token inválido ou expirado.",
        "pass_mismatch": "As senhas não conferem.",
        "uid_invalid": "UID inválido ou malformado."
    }

    def validate(self, attrs):
        uid = attrs.get("uid")
        token = attrs.get("token")
        new_pass = attrs.get("new_pass")
        new_pass_confirm = attrs.get("new_pass_confirm")
        
        # 1. Confirma que as senhas são iguais
        if new_pass != new_pass_confirm:
            logger.warning("Tentativa de redefinição com senhas diferentes para UID: %s", attrs.get("uid"))
            self.fail("pass_mismatch")

        # 2. Decodifica UID (já validado em validate_uid)
        try:
            decoded_uid = force_str(urlsafe_base64_decode(uid))
        except (ValueError, TypeError):
            self.fail("uid_invalid")

        # 3. Busca o usuário pelo UID decodificado
        try:
            user = User.objects.get(pk=decoded_uid)
        except User.DoesNotExist:
            logger.warning("Tentativa de redefinição para usuário inexistente UID: %s", decoded_uid)
            self.fail("user_not_found")
        except ValueError:
            # Caso o UID não seja um número válido
            logger.warning("UID não numérico fornecido: %s", decoded_uid)
            self.fail("uid_invalid")

        # 4. Valida token
        if not default_token_generator.check_token(user, token):
            logger.warning("Token inválido usado para usuário ID: %s", user.id)
            self.fail("token_invalid")


        attrs["user"] = user
        
        # 8. Remove campos desnecessários dos dados retornados
        attrs.pop("new_pass_confirm", None)
        attrs.pop("uid", None)  # Não precisamos mais do UID, temos o user
        
        logger.info("Validação bem-sucedida para redefinição de senha do usuário ID: %s", user.id)
        
        return attrs