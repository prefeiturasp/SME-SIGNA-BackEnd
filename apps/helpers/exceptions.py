class AuthenticationError(Exception):
    """Erro de autenticação personalizado."""

    pass


class CargoNotFoundError(Exception):
    """Erro quando cargo não é encontrado."""

    pass


class CessacaoNotFoundError(Exception):
    """Erro quando cessação não é encontrada."""

    pass


class InternalError(Exception):
    """Erro interno do sistema."""

    pass


class EmailNaoCadastradoError(Exception):
    """Email não cadastrado."""

    pass


class SmeIntegracaoError(Exception):
    """Problema na integração com a SME."""

    pass


class CargaUsuarioError(Exception):
    """Erro ao cadastrar usuário no CoreSSO."""

    pass


class TokenJaUtilizadoError(Exception):
    """Token de validação já foi usado."""

    pass


class TokenExpiradoError(Exception):
    """Token de validação expirou."""

    pass


class UserNotFoundError(Exception):
    """Erro quando usuário não é encontrado."""

    def __init__(self, message: str, usuario: object = None) -> None:
        super().__init__(message, usuario)
        self.usuario = usuario

    def __str__(self) -> str:
        return str(self.args[0])


class PerfilNaoAutorizadoError(Exception):
    """Não possui perfil signa."""

    pass
