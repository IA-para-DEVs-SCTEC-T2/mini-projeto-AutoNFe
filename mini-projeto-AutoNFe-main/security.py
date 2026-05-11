"""
Módulo de segurança — autenticação, headers e sanitização.
Centraliza todas as proteções da aplicação.
"""

from __future__ import annotations

import logging
import os
import re
import secrets
from functools import wraps
from typing import Callable

from flask import Flask, jsonify, request

# ---------------------------------------------------------------------------
# Logger de auditoria
# ---------------------------------------------------------------------------

logger = logging.getLogger("nfe.auditoria")


def configurar_logging() -> None:
    """Configura logging estruturado para auditoria de segurança."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


# ---------------------------------------------------------------------------
# Autenticação por token (A01 / A07)
# ---------------------------------------------------------------------------

# Token lido de variável de ambiente; gerado automaticamente se ausente
_API_TOKEN: str = os.environ.get("NFE_API_TOKEN", "")

if not _API_TOKEN:
    _API_TOKEN = secrets.token_hex(32)
    logger.warning(
        "NFE_API_TOKEN não definido. Token temporário gerado: %s  "
        "— Defina a variável de ambiente para uso em produção.",
        _API_TOKEN,
    )


def requer_autenticacao(f: Callable) -> Callable:
    """
    Decorator que exige o header 'X-API-Token' com o valor correto.
    Retorna 401 se ausente ou inválido.
    Usa comparação em tempo constante para evitar timing attacks.
    """
    @wraps(f)
    def _verificar(*args, **kwargs):
        token_recebido = request.headers.get("X-API-Token", "")
        if not secrets.compare_digest(token_recebido, _API_TOKEN):
            logger.warning(
                "Acesso negado — ip=%s rota=%s método=%s",
                request.remote_addr,
                request.path,
                request.method,
            )
            return jsonify({"erro": "Não autorizado."}), 401
        return f(*args, **kwargs)
    return _verificar


# ---------------------------------------------------------------------------
# Headers de segurança HTTP (A05)
# ---------------------------------------------------------------------------

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "   # necessário para onclick inline
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self';"
    ),
}


def registrar_headers_seguranca(app: Flask) -> None:
    """Adiciona headers de segurança em todas as respostas HTTP."""
    @app.after_request
    def _adicionar_headers(response):
        for header, valor in _SECURITY_HEADERS.items():
            response.headers[header] = valor
        return response


# ---------------------------------------------------------------------------
# Sanitização de nomes de arquivo (A08)
# ---------------------------------------------------------------------------

_NOME_ARQUIVO_PERMITIDO = re.compile(r"[^a-zA-Z0-9._\-]")
_TAMANHO_MAX_NOME = 100


def sanitizar_nome_arquivo(nome: str) -> str:
    """
    Remove caracteres não permitidos do nome do arquivo.
    Previne XSS e path traversal ao renderizar o nome no frontend.
    """
    # Remove separadores de path antes de sanitizar
    nome_base = os.path.basename(nome.replace("\\", "/"))
    nome_limpo = _NOME_ARQUIVO_PERMITIDO.sub("_", nome_base)
    # Remove sequências de pontos que poderiam indicar path traversal
    while ".." in nome_limpo:
        nome_limpo = nome_limpo.replace("..", "_")
    return nome_limpo[:_TAMANHO_MAX_NOME] or "arquivo.xml"


# ---------------------------------------------------------------------------
# Limite de arquivos no lote (A04)
# ---------------------------------------------------------------------------

MAX_ARQUIVOS_LOTE = int(os.environ.get("NFE_MAX_ARQUIVOS_LOTE", "50"))


# ---------------------------------------------------------------------------
# Logging de auditoria de operações
# ---------------------------------------------------------------------------

def log_importacao(nome_arquivo: str, sucesso: bool, ip: str) -> None:
    if sucesso:
        logger.info("Importação OK — arquivo=%s ip=%s", nome_arquivo, ip)
    else:
        logger.warning("Importação FALHOU — arquivo=%s ip=%s", nome_arquivo, ip)


def log_autorizacao(entidade: str, ids: list, ip: str) -> None:
    logger.info(
        "Autorização — entidade=%s ids=%s ip=%s",
        entidade, ids, ip,
    )
