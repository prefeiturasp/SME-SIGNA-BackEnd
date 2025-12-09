class AuthenticationError(Exception):
    """Erro de autenticação personalizado"""
    pass

class CargoNotFoundError(Exception):
    """Erro quando cargo não é encontrado"""
    pass

class InternalError(Exception):
    """Erro interno do sistema"""
    pass

class EmailNaoCadastrado(Exception):
    """Email não cadastrado"""
    pass

class SmeIntegracaoException(Exception):
    """Problema na integração com a SME"""
    pass

class CargaUsuarioException(Exception):
    """Erro ao cadastrar usuário no CoreSSO"""
    pass

class TokenJaUtilizadoException(Exception):
    """Token de validação já foi usado."""
    pass

class TokenExpiradoException(Exception):
    """Token de validação expirou."""
    pass