# SME-SIGNA-BackEnd
# Backend - Django + Django Rest Framework SME - SiGNA

## 🥞 Stack
- [Python v3.14](https://www.python.org/doc/)
- [Django v5.2](https://www.djangoproject.com/start/)
- [Django Rest Framework v3.17](https://www.django-rest-framework.org/)
- [Postgres v15](https://www.postgresql.org/docs/)
- [Pytest v9.1](https://docs.pytest.org/en/stable/)

## 🛠️ Configurando o projeto

Primeiro, clone o projeto:

### 🔄 via HTTPS
    $ git clone ...

### 🔐 via SSH
    $ ...

### 🐍 Criando e ativando uma virtual env
    $ python -m venv venv
    $ source venv/bin/activate  # Linux/macOS
    $ # ou venv\Scripts\activate no Windows

### 📦 Instalando as dependências do projeto
    $ pip install -r requirements/local.txt
    $ pre-commit install

### 📦 Instalando as dependências do projeto de teste
    $ pip install -r requirements/test.txt  

### 🔄 Apagando e recriando o venv após atualizar o requirements

Sempre que as versões em `requirements/*.txt` forem atualizadas (principalmente
majors, ou a versão do Python), é recomendado recriar o venv do zero em vez de
só rodar `pip install...` de novo sobre o existente, para evitar pacotes órfãos
de versões antigas.

    $ deactivate                     # se o venv atual estiver ativo
    $ mv venv venv.bak                # opcional: guarda o venv antigo como backup
    $ python -m venv venv
    $ source venv/bin/activate       # Linux/macOS
    $ # ou venv\Scripts\activate no Windows
    $ pip install --upgrade pip
    $ pip install -r requirements/local.txt
    $ pytest                         # valida se tudo ainda funciona
    $ rm -rf venv.bak                # depois de validar, remove o backup

> **_IMPORTANTE:_** o `pip install` só instala pacotes Python — ele **não**
> troca a versão do próprio Python. Se a versão do Python também mudou (ex:
> `Stack` acima), primeiro instale o interpretador da nova versão no seu
> sistema (ex: `pyenv install 3.14.6`), depois recrie o venv usando esse
> binário, ex: `python3.14 -m venv venv` (ou
> `~/.pyenv/versions/3.14.6/bin/python3 -m venv venv`), e só então rode o
> `pip install` normalmente dentro desse venv novo.

### 🗃️ Criando um banco do dados PostgreSQL usando createdb ou utilizando seu client preferido (pgAdmin, DBeaver...)
    $ createdb --username=postgres <project_slug>

### 🗃️ ou execute o container docker com o banco
    docker compose -f docker-compose.dev.yml up -d

> **_IMPORTANTE:_** Crie na raiz do projeto o arquivo _.env_ com base no .env.sample.
> Depois, em um terminal digite export DJANGO_READ_DOT_ENV_FILE=True e todas as variáveis serão lidas.

### ⚙️ Rodando as migrações
    $ python manage.py migrate

### 🚀 Executando o projeto
    $ python manage.py runserver

Feito tudo isso, o projeto estará executando no endereço [localhost:8000](http://localhost:8000).

### 👑 Opcional: Criando um super usuário
    $ python manage.py createsuperuser

### 🧪 Executando os testes com Pytest
    $ pytest

### 🧪 Executando a cobertura dos testes
    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html
    $ pytest --cov=apps --cov-report=term-missing

### 📚 Gerando e visualizando a documentação (Sphinx)
    $ python -m sphinx -b html docs docs/_build/html

O Sphinx gera arquivos HTML estáticos — não roda junto com o
`manage.py runserver`. Para visualizar, suba um servidor separado apontando
para a pasta gerada (em outro terminal, deixando o Django na porta 8000):

    $ cd docs/_build/html && python3 -m http.server 8080

Depois acesse [127.0.0.1:8080](http://127.0.0.1:8080/).

Alternativa com rebuild automático a cada alteração nos arquivos `.rst`:

    $ pip install sphinx-autobuild
    $ sphinx-autobuild docs docs/_build/html --port 8080

### 📄 Licença
Este projeto está sob a licença (sua licença) - veja o arquivo [LICENSE](./LICENSE) para detalhes.

### 🧪 Executando relatório de cobertura PEPs

# Um app só
python manage.py gerar_relatorio_pep --app core

# Todos os apps + consolidado
python manage.py gerar_relatorio_pep --all

# Apps selecionados + consolidado
python manage.py gerar_relatorio_pep --only core usuarios designacao

# Customizando saída do consolidado
python manage.py gerar_relatorio_pep --all --output-dir docs/relatorios

### ✅ Validando o projeto
pre-commit run --all-files

