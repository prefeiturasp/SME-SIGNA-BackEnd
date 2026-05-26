class AuthenticationError(Exception):
    """Erro de autenticação personalizado"""


class CargoNotFoundError(Exception):
    """Erro quando cargo não é encontrado"""


class CessacaoNotFoundError(Exception):
    """Erro quando cessação não é encontrada"""


class InternalError(Exception):
    """Erro interno do sistema"""


class EmailNaoCadastrado(Exception):
    """Email não cadastrado"""


class SmeIntegracaoException(Exception):
    """Problema na integração com a SME"""


class CargaUsuarioException(Exception):
    """Erro ao cadastrar usuário no CoreSSO"""


class TokenJaUtilizadoException(Exception):
    """Token de validação já foi usado."""


class TokenExpiradoException(Exception):
    """Token de validação expirou."""


class UserNotFoundError(Exception):
    """Erro quando usuário não é encontrado"""

    def __init__(self, message, usuario=None):
        super().__init__(message)
        self.usuario = usuario


class PerfilNaoAutorizadoError(Exception):
    """Não possui perfil signa"""
