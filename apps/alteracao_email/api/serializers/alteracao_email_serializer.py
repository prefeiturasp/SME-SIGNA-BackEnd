"""Serializador para validação de solicitação de alteração de e-mail.

Este módulo contém o serializador responsável por verificar se o novo e-mail
é válido, se ele não é igual ao e-mail atual, se pertence ao domínio
institucional e se não está em uso por outro usuário.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from rest_framework import serializers

from apps.usuarios.models import User


class AlteracaoEmailSerializer(serializers.Serializer):
    """Valida os dados de entrada para a alteração de e-mail.

    O serializador verifica se o novo e-mail está presente, se não é igual ao
    e-mail atual do usuário, se pertence ao domínio institucional e se já não
    está cadastrado no sistema.
    """

    new_email = serializers.CharField(
        required=True,
        error_messages={
            "blank": "O campo de e-mail é obrigatório.",
            "required": "O campo de e-mail é obrigatório.",
        },
    )

    def is_valid(self, raise_exception: bool = False) -> bool:
        """Valida o serializer e normaliza o formato de erro.

        Substitui os erros padrão do serializer por um dicionário contendo a
        chave "detail" com a primeira mensagem de erro encontrada.

        Args:
            raise_exception (bool): Se True, lança ValidationError quando
            houver
                erros de validação.

        Returns:
            bool: True se os dados são válidos, False caso contrário.
        """

        valid = super().is_valid(raise_exception=False)
        if not valid:

            first_error = next(iter(self.errors.values()))
            message = (
                first_error[0]
                if isinstance(first_error, list)
                else str(first_error)
            )

            self._errors = {"detail": message}

            if raise_exception:
                raise serializers.ValidationError(self._errors)

        return valid

    def validate_new_email(self, value: str) -> str:
        """Valida o novo e-mail recebido pelo serializer.

        Verifica se o novo e-mail não é igual ao atual, se pertence ao domínio
        institucional, se já não está cadastrado e se está em um formato
        válido.

        Args:
            value (str): O novo endereço de e-mail informado pelo usuário.

        Returns:
            str: O valor validado do e-mail.

        Raises:
            serializers.ValidationError: Se o e-mail for igual ao atual, não
                pertencer ao domínio institucional, já estiver cadastrado ou
                não for válido.
        """

        usuario = self.context["request"].user
        if usuario.email == value:
            raise serializers.ValidationError(
                "O novo e-mail não pode ser igual ao atual."
            )

        if not value.endswith("@sme.prefeitura.sp.gov.br"):
            raise serializers.ValidationError(
                "Utilize seu e-mail institucional."
            )

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Este e-mail já está cadastrado."
            )

        try:
            validate_email(value)

        except DjangoValidationError as exc:
            raise serializers.ValidationError(
                "Digite um e-mail válido!"
            ) from exc

        return value
