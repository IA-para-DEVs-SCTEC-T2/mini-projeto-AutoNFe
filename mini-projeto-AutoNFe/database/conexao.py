"""
Módulo de conexão com o banco de dados SQLite.

SEGURANÇA:
- Todas as queries usam parâmetros posicionais (?) — nunca concatenação de string.
- Permissões do arquivo .db definidas como 600 atomicamente na criação,
  usando os.open(O_CREAT | O_EXCL, 0o600) — elimina a race condition (TOCTOU)
  que existiria entre sqlite3.connect() e um chmod() posterior.
- No Windows o chmod POSIX não tem efeito; o arquivo fica acessível
  normalmente para o usuário corrente (ex: DBeaver).
- Sem execução de SQL dinâmico ou construção de queries por f-string.
"""

import os
import sqlite3
from pathlib import Path


_DB_PATH = Path(os.environ.get("DB_PATH", "autonfe.db")).resolve()


def _criar_arquivo_db_seguro(caminho: Path) -> None:
    """
    Cria o arquivo .db com permissões 600 atomicamente.

    Usa os.O_CREAT | os.O_EXCL para garantir criação exclusiva —
    falha se o arquivo já existir, evitando sobrescrever um banco existente.
    O modo 0o600 é aplicado no momento da criação, sem janela de tempo
    entre criar e restringir (eliminando a race condition TOCTOU).

    No Windows o modo POSIX é ignorado pelo SO; o comportamento é o
    padrão do sistema de arquivos NTFS para o usuário corrente.

    Args:
        caminho: Path absoluto onde o arquivo será criado.
    """
    try:
        fd = os.open(
            str(caminho),
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,  # somente dono: leitura + escrita (Linux/macOS)
        )
        os.close(fd)
    except FileExistsError:
        # Outro processo criou o arquivo entre a verificação e a criação;
        # não é um erro — o banco já existe e será aberto normalmente.
        pass


def obter_conexao() -> sqlite3.Connection:
    """
    Retorna uma conexão com o banco de dados SQLite.

    - Se o arquivo não existir, cria-o com permissões 600 antes de conectar.
    - Habilita chaves estrangeiras (PRAGMA foreign_keys = ON).
    - Usa Row como row_factory para acesso por nome de coluna.

    Returns:
        Conexão SQLite configurada.
    """
    if not _DB_PATH.exists():
        _criar_arquivo_db_seguro(_DB_PATH)

    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_banco() -> None:
    """
    Cria as tabelas do banco de dados caso ainda não existam.
    Executar uma vez na inicialização da aplicação.
    """
    with obter_conexao() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS emitente (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                cnpj        TEXT    NOT NULL UNIQUE,
                razao_social TEXT   NOT NULL,
                ie          TEXT,
                status      TEXT    NOT NULL DEFAULT 'PENDENTE',
                criado_em   TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS destinatario (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                cnpj        TEXT,
                cpf         TEXT,
                razao_social TEXT   NOT NULL,
                ie          TEXT,
                status      TEXT    NOT NULL DEFAULT 'PENDENTE',
                criado_em   TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS tributacao (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                cfop        TEXT    NOT NULL,
                cst_csosn   TEXT    NOT NULL,
                aliquota    TEXT    NOT NULL,
                status      TEXT    NOT NULL DEFAULT 'PENDENTE',
                criado_em   TEXT    NOT NULL DEFAULT (datetime('now')),
                UNIQUE (cfop, cst_csosn, aliquota)
            );

            CREATE TABLE IF NOT EXISTS nfe (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                chave_acesso TEXT   NOT NULL UNIQUE,
                emitente_id INTEGER NOT NULL REFERENCES emitente(id),
                destinatario_id INTEGER NOT NULL REFERENCES destinatario(id),
                valor_total TEXT    NOT NULL,
                importado_em TEXT   NOT NULL DEFAULT (datetime('now'))
            );
        """)
