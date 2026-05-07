"""
Módulo de autenticação — login, sessão, cadastro de usuários e recuperação de senha.
"""

from __future__ import annotations

import logging
import re
import secrets
import string
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional

from flask import jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from src.database.models import SessionLocal, Usuario, criar_tabelas

logger = logging.getLogger("autonfe.auth")

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

SENHA_TEMP_VALIDADE_HORAS = 24
REGEX_SENHA_FORTE = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]).{8,}$'
)


# ---------------------------------------------------------------------------
# Helpers de senha
# ---------------------------------------------------------------------------

def validar_senha_forte(senha: str) -> list[str]:
    """Retorna lista de erros; lista vazia = senha válida."""
    erros = []
    if len(senha) < 8:
        erros.append("Mínimo 8 caracteres")
    if not re.search(r'[a-z]', senha):
        erros.append("Deve conter letra minúscula")
    if not re.search(r'[A-Z]', senha):
        erros.append("Deve conter letra maiúscula")
    if not re.search(r'\d', senha):
        erros.append("Deve conter número")
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', senha):
        erros.append("Deve conter caractere especial (!@#$%...)")
    return erros


def gerar_senha_temporaria(tamanho: int = 12) -> str:
    """Gera senha temporária aleatória que atende aos requisitos."""
    alfabeto = string.ascii_letters + string.digits + "!@#$%"
    while True:
        senha = ''.join(secrets.choice(alfabeto) for _ in range(tamanho))
        if not validar_senha_forte(senha):
            return senha


# ---------------------------------------------------------------------------
# Seed: cria usuário administrador padrão se não existir
# ---------------------------------------------------------------------------

def seed_admin():
    """Cria o usuário administrador inicial (login: admin / senha: sa)."""
    db = SessionLocal()
    try:
        existe = db.query(Usuario).filter_by(email="admin@autonfe.local").first()
        if not existe:
            admin = Usuario(
                nome="Administrador",
                email="admin@autonfe.local",
                senha_hash=generate_password_hash("sa"),
                tipo="administrador",
                ativo=True,
                trocar_senha=True,   # força troca no primeiro login
            )
            db.add(admin)
            db.commit()
            logger.info("Usuário administrador criado (login: admin@autonfe.local / senha: sa)")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Decorator: exige login
# ---------------------------------------------------------------------------

def login_requerido(f):
    @wraps(f)
    def _verificar(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return _verificar


def admin_requerido(f):
    @wraps(f)
    def _verificar(*args, **kwargs):
        if "usuario_id" not in session:
            return redirect(url_for("login"))
        if session.get("usuario_tipo") != "administrador":
            return jsonify({"erro": "Acesso restrito a administradores."}), 403
        return f(*args, **kwargs)
    return _verificar


# ---------------------------------------------------------------------------
# Funções de autenticação
# ---------------------------------------------------------------------------

def autenticar_usuario(login: str, senha: str) -> tuple[Optional[Usuario], str]:
    """
    Autentica por e-mail ou nome de usuário.
    Retorna (usuario, motivo_erro). Se sucesso, motivo_erro é ''.
    """
    db = SessionLocal()
    try:
        usuario = (
            db.query(Usuario)
            .filter(
                (Usuario.email == login) | (Usuario.nome == login)
            )
            .first()
        )
        if not usuario:
            return None, "Usuário não encontrado."
        if not usuario.ativo:
            return None, "Usuário inativo. Contate o administrador."

        # Verifica senha normal
        if check_password_hash(usuario.senha_hash, senha):
            return usuario, ""

        # Verifica senha temporária
        if usuario.senha_temp and check_password_hash(usuario.senha_temp, senha):
            return usuario, ""

        return None, "Senha incorreta."
    finally:
        db.close()
