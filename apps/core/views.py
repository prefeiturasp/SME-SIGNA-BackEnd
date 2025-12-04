from django.shortcuts import render

# Create your views here.
# apps/core/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Retorna informações básicas do usuário autenticado.
    Rota protegida — exige Authorization: Bearer <access_token>.
    """
    user = request.user
    data = {
        "id": user.id,
        "username": user.get_username(),
        "email": user.email,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
        # adicione mais campos se quiser (cuidado com dados sensíveis)
    }
    return Response(data)

@api_view(['GET'])
@permission_classes([AllowAny])
def debug_headers(request):
    keys = {k: v for k, v in request.META.items() if 'AUTH' in k or 'HTTP_AUTH' in k}
    return Response(keys)

@api_view(['GET'])
@permission_classes([AllowAny])
def debug_authenticate(request):
    """
    Tenta autenticar o request usando JWTAuthentication e mostra o resultado.
    Use curl para chamar /api/debug-auth/ com o Authorization header.
    """
    auth = JWTAuthentication()
    try:
        result = auth.authenticate(request)
        if result is None:
            return Response({"authenticate": None, "detail": "authenticate returned None"})
        user, validated_token = result
        return Response({
            "authenticate": "ok",
            "username": user.get_username(),
            "user_id": getattr(user, "id", None),
            "token_payload": validated_token.payload,
        })
    except Exception as e:
        return Response({"authenticate": "error", "error": str(e)})