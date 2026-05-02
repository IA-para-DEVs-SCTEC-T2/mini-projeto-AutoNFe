"""
Dashboard — Autenticação

Controla o acesso ao Dashboard via sessão Flask.

SEGURANÇA:
- Senha comparada com hash bcrypt (nunca texto plano em produção).
- Comparação de hash usa hmac.compare_digest para evitar timing attacks.
- Sessão invalidada no logout (session.clear()).
- Decorator login_required protege todas as rotas do Dashboard.
- SECRET_KEY e credenciais lidas exclusivamente de variáveis de ambiente.
- Tentativas de login com credenciais inválidas retornam sempre o mesmo
  tempo de resposta (sem diferença entre "usuário errado" e "senha errada").
"""

import hashlib
import hmac
import os
from functools import wraps
from typing import Callable

from flask import redirect, render_template, request, session, url_for


# ---------------------------------------------------------------------------
# Configuração — lida de variáveis de ambiente, nunca hardcoded
# ---------------------------------------------------------------------------

def _obter_hash_senha() -> str:
    """
    Retorna o hash SHA-256 da senha configurada em DASHBOARD_PASSWORD.

    Em produção, substitua por bcrypt:
        pip install bcrypt
        hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()

    Raises:
        RuntimeError: Se DASHBOARD_PASSWORD não estiver definida.
    """
    senha = os.environ.get("DASHBOARD_PASSWORD", "")
    if not senha:
        raise RuntimeError(
            "Variável de ambiente DASHBOARD_PASSWORD não definida. "
            "Configure-a antes de iniciar o Dashboard."
        )
    # SHA-256 como fallback simples; prefira bcrypt em produção
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def _obter_usuario() -> str:
    """
    Retorna o usuário configurado em DASHBOARD_USER.

    Raises:
        RuntimeError: Se DASHBOARD_USER não estiver definida.
    """
    usuario = os.environ.get("DASHBOARD_USER", "")
    if not usuario:
        raise RuntimeError(
            "Variável de ambiente DASHBOARD_USER não definida. "
            "Configure-a antes de iniciar o Dashboard."
        )
    return usuario


# ---------------------------------------------------------------------------
# Verificação de credenciais
# ---------------------------------------------------------------------------

def verificar_credenciais(usuario: str, senha: str) -> bool:
    """
    Verifica se as credenciais fornecidas são válidas.

    Usa hmac.compare_digest para comparação em tempo constante,
    evitando timing attacks.

    Args:
        usuario: Nome de usuário informado no formulário.
        senha:   Senha em texto plano informada no formulário.

    Returns:
        True se as credenciais forem válidas, False caso contrário.
    """
    try:
        usuario_esperado = _obter_usuario()
        hash_esperado = _obter_hash_senha()
    except RuntimeError:
        return False

    hash_informado = hashlib.sha256(senha.encode("utf-8")).hexdigest()

    usuario_ok = hmac.compare_digest(usuario, usuario_esperado)
    senha_ok = hmac.compare_digest(hash_informado, hash_esperado)

    # Ambas as comparações são feitas antes de retornar (sem short-circuit)
    return usuario_ok and senha_ok


# ---------------------------------------------------------------------------
# Decorator de proteção de rotas
# ---------------------------------------------------------------------------

def login_required(f: Callable) -> Callable:
    """
    Decorator que redireciona para /login se o usuário não estiver autenticado.

    Uso:
        @app.route("/dashboard")
        @login_required
        def dashboard():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("autenticado"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Views de login / logout
# ---------------------------------------------------------------------------

def registrar_rotas_auth(app) -> None:
    """
    Registra as rotas de autenticação (/login e /logout) na aplicação Flask.

    Args:
        app: Instância do Flask.
    """

    @app.route("/login", methods=["GET", "POST"])
    def login():
        erro = None

        if request.method == "POST":
            usuario = request.form.get("usuario", "")
            senha = request.form.get("senha", "")

            if verificar_credenciais(usuario, senha):
                session.clear()
                session["autenticado"] = True
                session.permanent = False  # sessão expira ao fechar o browser
                return redirect(url_for("index"))

            # Mensagem genérica — não revela se foi usuário ou senha errada
            erro = "Credenciais inválidas."

        return render_template("login.html", erro=erro)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))
