# SME-SIGNA-BackEnd
# Backend - Django + Django Rest Framework SME - SiGNA

## 🥞 Stack
- [Python v3.12](https://www.python.org/doc/)
- [Django v5.1.8](https://www.djangoproject.com/start/)
- [Django Rest Framework v3.16](https://www.django-rest-framework.org/)
- [Postgres v16.4](https://www.postgresql.org/docs/)
- [Pytest v8.3.5](https://docs.pytest.org/en/stable/)

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

### 📦 Instalando as dependências do projeto de teste
    $ pip install -r requirements/test.txt  

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

