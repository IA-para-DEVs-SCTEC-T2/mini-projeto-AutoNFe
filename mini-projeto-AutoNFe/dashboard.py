"""
AutoNFe — Dashboard

Servidor Flask do painel de controle.

SEGURANÇA:
- SECRET_KEY lida de variável de ambiente (nunca hardcoded).
- Todas as rotas protegidas pelo decorator @login_required.
- Sessão não permanente (expira ao fechar o browser).
- Bind em 127.0.0.1 por padrão (não expõe para a rede local).

Uso:
    python dashboard.py
"""

import os
import sys

from dotenv import load_dotenv
load_dotenv()  # carrega variáveis do .env antes de qualquer import do projeto

from flask import Flask, render_template

from database.conexao import inicializar_banco
from dashboard.auth import login_required, registrar_rotas_auth


def criar_app() -> Flask:
    secret_key = os.environ.get("SECRET_KEY", "")
    if not secret_key:
        print(
            "[ERRO] Variável de ambiente SECRET_KEY não definida.\n"
            "Gere um valor com: python -c \"import secrets; print(secrets.token_hex(32))\"\n"
            "e adicione ao seu arquivo .env.",
            file=sys.stderr,
        )
        sys.exit(1)

    app = Flask(__name__, template_folder="templates")
    app.secret_key = secret_key

    # Configurações de segurança da sessão
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,   # JS não acessa o cookie de sessão
        SESSION_COOKIE_SAMESITE="Lax",  # proteção básica contra CSRF
        SESSION_COOKIE_SECURE=os.environ.get("APP_ENV") == "production",
    )

    # Registra rotas de autenticação (/login, /logout)
    registrar_rotas_auth(app)

    # ---------------------------------------------------------------------------
    # Rotas protegidas
    # ---------------------------------------------------------------------------

    @app.route("/")
    @login_required
    def index():
        return render_template("dashboard.html")

    return app


if __name__ == "__main__":
    inicializar_banco()

    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    port = int(os.environ.get("DASHBOARD_PORT", "5000"))
    debug = os.environ.get("APP_ENV", "development") == "development"

    app = criar_app()
    app.run(host=host, port=port, debug=debug)
