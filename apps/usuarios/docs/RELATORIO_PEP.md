# Relatório PEP — app `usuarios`

Gerado em: **2026-05-21 13:04:46 UTC**  
Commit: `e050c33`  
Limite linha (PEP 8): **79**

## Resumo
| Métrica | Valor | % |
| --- | ---: | ---: |
| Arquivos | 22 | — |
| LOC | 3660 | — |
| Linhas > 79 | 67 | 1.8% |
| Funções/métodos | 177 | — |
| Com docstring | 50 | 28.2% |
| Classes c/ docstring | 7/30 | 23.3% |
| Hints completos | 10 | 5.6% |
| flake8 | 75 | — |

### Top flake8

| Código | Ocorrências |
| --- | ---: |
| `E501` | 68 |
| `F841` | 7 |

<details><summary>Primeiras 30 linhas flake8</summary>

```
apps/usuarios/__tests__/test_login_view.py:139:80: E501 line too long (86 > 79 characters)
apps/usuarios/__tests__/test_login_view.py:151:80: E501 line too long (100 > 79 characters)
apps/usuarios/__tests__/test_login_view.py:162:80: E501 line too long (86 > 79 characters)
apps/usuarios/__tests__/test_login_view.py:182:80: E501 line too long (86 > 79 characters)
apps/usuarios/__tests__/test_login_view.py:210:80: E501 line too long (86 > 79 characters)
apps/usuarios/__tests__/test_login_view.py:241:80: E501 line too long (86 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:64:80: E501 line too long (88 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:67:80: E501 line too long (80 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:97:80: E501 line too long (88 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:100:80: E501 line too long (80 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:125:80: E501 line too long (88 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:128:80: E501 line too long (80 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:136:9: F841 local variable 'user' is assigned to but never used
apps/usuarios/__tests__/test_senha_view.py:157:80: E501 line too long (88 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:172:80: E501 line too long (88 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:176:9: F841 local variable 'user' is assigned to but never used
apps/usuarios/__tests__/test_senha_view.py:199:80: E501 line too long (88 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:222:80: E501 line too long (80 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:253:9: F841 local variable 'user_7' is assigned to but never used
apps/usuarios/__tests__/test_senha_view.py:262:9: F841 local variable 'user_8' is assigned to but never used
apps/usuarios/__tests__/test_senha_view.py:277:80: E501 line too long (91 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:284:9: F841 local variable 'user' is assigned to but never used
apps/usuarios/__tests__/test_senha_view.py:295:9: F841 local variable 'user' is assigned to but never used
apps/usuarios/__tests__/test_senha_view.py:305:80: E501 line too long (88 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:310:80: E501 line too long (96 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:325:80: E501 line too long (88 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:328:80: E501 line too long (80 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:336:9: F841 local variable 'user' is assigned to but never used
apps/usuarios/__tests__/test_senha_view.py:364:80: E501 line too long (88 > 79 characters)
apps/usuarios/__tests__/test_senha_view.py:367:80: E501 line too long (80 > 79 characters)
```
<​/details>

## Símbolos sem docstring (top)

| Arquivo | Linha | Símbolo | Tipo |
| --- | ---: | --- | --- |
| `__tests__/conftest.py` | 53 | `mock_sme_auth_error` | function |
| `__tests__/conftest.py` | 54 | `fake_autentica` | function |
| `__tests__/test_envia_email_service.py` | 12 | `use_locmem_email_backend` | function |
| `__tests__/test_envia_email_service.py` | 18 | `TestEnviaEmailService` | class |
| `__tests__/test_envia_email_service.py` | 20 | `TestEnviaEmailService.email_data` | function |
| `__tests__/test_envia_email_service.py` | 28 | `TestEnviaEmailService.test_send_email_success` | function |
| `__tests__/test_envia_email_service.py` | 39 | `TestEnviaEmailService.test_send_email_empty_destinatario_raises` | function |
| `__tests__/test_envia_email_service.py` | 44 | `TestEnviaEmailService.test_send_email_empty_assunto_raises` | function |
| `__tests__/test_envia_email_service.py` | 49 | `TestEnviaEmailService.test_send_email_unexpected_exception_raises_runtimeerror` | function |
| `__tests__/test_login_view.py` | 16 | `set_signa_env` | function |
| `__tests__/test_login_view.py` | 21 | `test_login_success` | function |
| `__tests__/test_login_view.py` | 46 | `test_login_unauthorized` | function |
| `__tests__/test_login_view.py` | 61 | `test_login_sme_error` | function |
| `__tests__/test_login_view.py` | 76 | `test_login_sme_exception` | function |
| `__tests__/test_login_view.py` | 91 | `test_login_updates_existing_user` | function |
| `__tests__/test_login_view.py` | 121 | `test_login_authentication_error` | function |
| `__tests__/test_login_view.py` | 133 | `test_login_sme_integracao_exception` | function |
| `__tests__/test_login_view.py` | 156 | `test_login_generic_exception` | function |
| `__tests__/test_login_view.py` | 175 | `test_login_perfil_nao_autorizado_sem_perfis` | function |
| `__tests__/test_login_view.py` | 203 | `test_login_perfil_nao_autorizado_perfis_nao_lista` | function |
| `__tests__/test_login_view.py` | 232 | `test_login_perfil_nao_autorizado_codigo_signa_nao_presente` | function |
| `__tests__/test_me_viewset.py` | 13 | `test_me_view_authenticated_user_returns_user_data` | function |
| `__tests__/test_senha_serializer.py` | 16 | `TestRedefinirSenhaSerializer` | class |
| `__tests__/test_senha_serializer.py` | 18 | `TestRedefinirSenhaSerializer.test_serializer_valid_data` | function |
| `__tests__/test_senha_serializer.py` | 44 | `TestRedefinirSenhaSerializer.test_serializer_password_mismatch` | function |

## PEP 440
- Arquivos: base.txt, local.txt, production.txt, test.txt
- Linhas: **26**
- PyPI válidas: **26**
- git+: **0**
- ==: **5**
- Inválidas: **0**

## Por arquivo
| Arquivo | LOC | >max | Funções | Doc % | Hints completos % |
| --- | ---: | ---: | ---: | ---: | ---: |
| `__init__.py` | 0 | 0 | 0 | — | — |
| `__tests__/conftest.py` | 57 | 0 | 6 | 66.7% | 0.0% |
| `__tests__/test_envia_email_service.py` | 59 | 0 | 6 | 0.0% | 0.0% |
| `__tests__/test_login_view.py` | 262 | 6 | 12 | 0.0% | 0.0% |
| `__tests__/test_me_viewset.py` | 36 | 0 | 1 | 0.0% | 0.0% |
| `__tests__/test_senha_serializer.py` | 144 | 0 | 6 | 16.7% | 0.0% |
| `__tests__/test_senha_view.py` | 899 | 38 | 38 | 63.2% | 0.0% |
| `__tests__/test_sme_integracao_service.py` | 775 | 4 | 67 | 6.0% | 0.0% |
| `__tests__/test_usuarios_models.py` | 44 | 0 | 3 | 0.0% | 0.0% |
| `admin.py` | 12 | 0 | 0 | — | — |
| `api/serializers/login_serializer.py` | 22 | 0 | 1 | 0.0% | 0.0% |
| `api/serializers/me_serializer.py` | 16 | 0 | 0 | — | — |
| `api/serializers/senha_serializer.py` | 132 | 1 | 3 | 0.0% | 0.0% |
| `api/views/login_view.py` | 144 | 2 | 4 | 25.0% | 0.0% |
| `api/views/me_view.py` | 21 | 0 | 1 | 0.0% | 0.0% |
| `api/views/senha_view.py` | 344 | 4 | 8 | 50.0% | 0.0% |
| `apps.py` | 7 | 0 | 0 | — | — |
| `models.py` | 36 | 0 | 2 | 50.0% | 0.0% |
| `services/envia_email_service.py` | 55 | 1 | 3 | 33.3% | 0.0% |
| `services/senha_service.py` | 47 | 0 | 2 | 100.0% | 0.0% |
| `services/sme_integracao_service.py` | 519 | 11 | 14 | 57.1% | 71.4% |
| `urls.py` | 29 | 0 | 0 | — | — |

*Gerado por `python manage.py gerar_relatorio_pep --app usuarios`*
