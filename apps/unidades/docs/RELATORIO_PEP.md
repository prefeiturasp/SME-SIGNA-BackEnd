# Relatório PEP — app `unidades`

Gerado em: **2026-05-21 13:04:45 UTC**  
Commit: `e050c33`  
Limite linha (PEP 8): **79**

## Resumo
| Métrica | Valor | % |
| --- | ---: | ---: |
| Arquivos | 11 | — |
| LOC | 1818 | — |
| Linhas > 79 | 26 | 1.4% |
| Funções/métodos | 104 | — |
| Com docstring | 65 | 62.5% |
| Classes c/ docstring | 6/19 | 31.6% |
| Hints completos | 8 | 7.7% |
| flake8 | 27 | — |

### Top flake8

| Código | Ocorrências |
| --- | ---: |
| `E501` | 27 |

<details><summary>Primeiras 30 linhas flake8</summary>

```
apps/unidades/__tests__/test_unidades_view.py:46:80: E501 line too long (80 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:71:80: E501 line too long (80 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:88:80: E501 line too long (80 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:101:80: E501 line too long (80 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:117:80: E501 line too long (80 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:133:80: E501 line too long (105 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:136:80: E501 line too long (112 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:169:80: E501 line too long (105 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:172:80: E501 line too long (112 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:188:80: E501 line too long (105 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:191:80: E501 line too long (112 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:206:80: E501 line too long (105 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:209:80: E501 line too long (112 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:231:80: E501 line too long (105 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:234:80: E501 line too long (112 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:254:80: E501 line too long (105 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:257:80: E501 line too long (112 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:276:80: E501 line too long (105 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:279:80: E501 line too long (112 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:299:80: E501 line too long (105 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:302:80: E501 line too long (112 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:332:80: E501 line too long (105 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:335:80: E501 line too long (112 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:340:80: E501 line too long (90 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:354:80: E501 line too long (81 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:396:80: E501 line too long (80 > 79 characters)
apps/unidades/__tests__/test_unidades_view.py:412:80: E501 line too long (80 > 79 characters)
```
<​/details>

## Símbolos sem docstring (top)

| Arquivo | Linha | Símbolo | Tipo |
| --- | ---: | --- | --- |
| `__tests__/conftest.py` | 264 | `_create_response` | function |
| `__tests__/conftest.py` | 278 | `_create_response` | function |
| `__tests__/conftest.py` | 295 | `_config` | function |
| `__tests__/test_unidades_service.py` | 19 | `TestBaseEOLService` | class |
| `__tests__/test_unidades_service.py` | 22 | `TestBaseEOLService.test_get_sucesso_dict` | function |
| `__tests__/test_unidades_service.py` | 32 | `TestBaseEOLService.test_get_401` | function |
| `__tests__/test_unidades_service.py` | 39 | `TestBaseEOLService.test_get_404` | function |
| `__tests__/test_unidades_service.py` | 46 | `TestBaseEOLService.test_get_status_erro` | function |
| `__tests__/test_unidades_service.py` | 54 | `TestBaseEOLService.test_get_timeout` | function |
| `__tests__/test_unidades_service.py` | 61 | `TestBaseEOLService.test_get_request_exception` | function |
| `__tests__/test_unidades_service.py` | 71 | `TestDREIntegracaoService` | class |
| `__tests__/test_unidades_service.py` | 75 | `TestDREIntegracaoService.test_get_dres` | function |
| `__tests__/test_unidades_service.py` | 87 | `TestDREIntegracaoService.test_get_dres_resposta_invalida` | function |
| `__tests__/test_unidades_service.py` | 97 | `TestDREIntegracaoService.test_get_dre_by_codigo_encontrada` | function |
| `__tests__/test_unidades_service.py` | 107 | `TestDREIntegracaoService.test_get_dre_by_codigo_none` | function |
| `__tests__/test_unidades_service.py` | 116 | `TestUnidadeIntegracaoService` | class |
| `__tests__/test_unidades_service.py` | 120 | `TestUnidadeIntegracaoService.test_get_unidades` | function |
| `__tests__/test_unidades_service.py` | 138 | `TestUnidadeIntegracaoService.test_get_unidades_codigo_invalido` | function |
| `__tests__/test_unidades_service.py` | 146 | `TestUnidadeIntegracaoService.test_get_unidades_resposta_invalida` | function |
| `__tests__/test_unidades_service.py` | 157 | `TestUnidadeIntegracaoService.test_get_escolas` | function |
| `__tests__/test_unidades_service.py` | 176 | `TestUnidadeIntegracaoService.test_get_codigo_integracao` | function |
| `__tests__/test_unidades_service.py` | 199 | `TestUnidadeSupervisao` | class |
| `__tests__/test_unidades_service.py` | 206 | `TestUnidadeSupervisao.test_sucesso` | function |
| `__tests__/test_unidades_service.py` | 233 | `TestUnidadeSupervisao.test_dre_codigo_invalido` | function |
| `__tests__/test_unidades_service.py` | 240 | `TestUnidadeSupervisao.test_sem_mapeamento` | function |

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
| `__tests__/conftest.py` | 334 | 0 | 23 | 87.0% | 0.0% |
| `__tests__/test_unidades_serializer.py` | 191 | 0 | 15 | 100.0% | 0.0% |
| `__tests__/test_unidades_service.py` | 362 | 0 | 28 | 0.0% | 0.0% |
| `__tests__/test_unidades_view.py` | 433 | 26 | 25 | 100.0% | 0.0% |
| `api/serializers/unidades_serializer.py` | 74 | 0 | 1 | 100.0% | 0.0% |
| `api/views/unidades_viewset.py` | 148 | 0 | 4 | 100.0% | 0.0% |
| `apps.py` | 6 | 0 | 0 | — | — |
| `constants/utils.py` | 15 | 0 | 0 | — | — |
| `services/unidades_service.py` | 241 | 0 | 8 | 0.0% | 100.0% |
| `urls.py` | 14 | 0 | 0 | — | — |

*Gerado por `python manage.py gerar_relatorio_pep --app unidades`*
