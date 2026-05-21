# Relatório PEP — app `alteracao_email`

Gerado em: **2026-05-21 13:04:45 UTC**  
Commit: `e050c33`  
Limite linha (PEP 8): **79**

## Resumo
| Métrica | Valor | % |
| --- | ---: | ---: |
| Arquivos | 8 | — |
| LOC | 269 | — |
| Linhas > 79 | 1 | 0.4% |
| Funções/métodos | 7 | — |
| Com docstring | 0 | 0.0% |
| Classes c/ docstring | 0/6 | 0.0% |
| Hints completos | 0 | 0.0% |
| flake8 | 1 | — |

### Top flake8

| Código | Ocorrências |
| --- | ---: |
| `E501` | 1 |

<details><summary>Primeiras 30 linhas flake8</summary>

```
apps/alteracao_email/api/views/alteracao_email_viewset.py:91:80: E501 line too long (86 > 79 characters)
```
<​/details>

## Símbolos sem docstring (top)

| Arquivo | Linha | Símbolo | Tipo |
| --- | ---: | --- | --- |
| `api/serializers/alteracao_email_serializer.py` | 8 | `AlteracaoEmailSerializer` | class |
| `api/serializers/alteracao_email_serializer.py` | 17 | `AlteracaoEmailSerializer.is_valid` | function |
| `api/serializers/alteracao_email_serializer.py` | 36 | `AlteracaoEmailSerializer.validate_new_email` | function |
| `api/views/alteracao_email_viewset.py` | 25 | `SolicitarAlteracaoEmailViewSet` | class |
| `api/views/alteracao_email_viewset.py` | 28 | `SolicitarAlteracaoEmailViewSet.create` | function |
| `api/views/alteracao_email_viewset.py` | 52 | `ValidarAlteracaoEmailViewSet` | class |
| `api/views/alteracao_email_viewset.py` | 55 | `ValidarAlteracaoEmailViewSet.update` | function |
| `apps.py` | 4 | `AlteracaoEmailConfig` | class |
| `models/alteracao_email.py` | 7 | `AlteracaoEmail` | class |
| `models/alteracao_email.py` | 16 | `AlteracaoEmail.__str__` | function |
| `services/alteracao_email_service.py` | 19 | `AlteracaoEmailService` | class |
| `services/alteracao_email_service.py` | 22 | `AlteracaoEmailService.solicitar` | function |
| `services/alteracao_email_service.py` | 43 | `AlteracaoEmailService.validar` | function |

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
| `api/serializers/alteracao_email_serializer.py` | 60 | 0 | 2 | 0.0% | 0.0% |
| `api/views/alteracao_email_viewset.py` | 104 | 1 | 2 | 0.0% | 0.0% |
| `apps.py` | 6 | 0 | 0 | — | — |
| `models/__init__.py` | 1 | 0 | 0 | — | — |
| `models/alteracao_email.py` | 17 | 0 | 1 | 0.0% | 0.0% |
| `services/alteracao_email_service.py` | 55 | 0 | 2 | 0.0% | 0.0% |
| `urls.py` | 26 | 0 | 0 | — | — |

*Gerado por `python manage.py gerar_relatorio_pep --app alteracao_email`*
