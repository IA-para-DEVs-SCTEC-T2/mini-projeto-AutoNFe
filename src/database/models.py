"""
Modelos SQLAlchemy para o banco de dados local (SQLite – open source).
"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer,
    Numeric, String, Text, create_engine, event
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker


def _agora():
    """Retorna o datetime local atual (sem timezone)."""
    return datetime.now()

# ---------------------------------------------------------------------------
# Engine SQLite (arquivo local)
# ---------------------------------------------------------------------------

import os

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(_BASE_DIR, "data", "database", "autonfe.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Garante que o diretório para o arquivo de banco exista antes de abrir/conectar
_DB_DIR = os.path.dirname(DB_PATH)
if not os.path.exists(_DB_DIR):
    try:
        os.makedirs(_DB_DIR, exist_ok=True)
    except OSError:
        # Falha ao criar o diretório — deixamos o erro pro SQLAlchemy para diagnóstico
        pass

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

# Habilita foreign keys no SQLite
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# ---------------------------------------------------------------------------
# Base declarativa
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Modelo: Usuário
# ---------------------------------------------------------------------------

class Usuario(Base):
    __tablename__ = "usuarios"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    nome          = Column(String(100), nullable=False)
    email         = Column(String(150), unique=True, nullable=False, index=True)
    senha_hash    = Column(String(256), nullable=False)
    tipo          = Column(String(20), nullable=False, default="padrao")  # "padrao" | "administrador"
    ativo         = Column(Boolean, default=True, nullable=False)
    # Controle de senha
    trocar_senha  = Column(Boolean, default=False, nullable=False)  # True = forçar troca no próximo login
    senha_temp    = Column(String(256), nullable=True)               # hash da senha temporária
    criado_em     = Column(DateTime, default=_agora)
    atualizado_em = Column(DateTime, default=_agora, onupdate=_agora)


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------

class Emitente(Base):
    __tablename__ = "emitentes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cnpj = Column(String(14), unique=True, nullable=True, index=True)
    cpf = Column(String(11), unique=True, nullable=True, index=True)
    nome = Column(String(150), nullable=False)
    fantasia = Column(String(150))
    ie = Column(String(30))
    crt = Column(String(1))
    logradouro = Column(String(200))
    numero = Column(String(20))
    complemento = Column(String(100))
    bairro = Column(String(100))
    municipio = Column(String(100))
    uf = Column(String(2))
    cep = Column(String(8))
    fone = Column(String(20))
    autorizado = Column(Boolean, default=False, nullable=False)
    criado_em = Column(DateTime, default=_agora)
    atualizado_em = Column(DateTime, default=_agora, onupdate=_agora)

    notas = relationship("NotaFiscal", back_populates="emitente_rel", foreign_keys="NotaFiscal.emitente_id")


class Destinatario(Base):
    __tablename__ = "destinatarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cnpj = Column(String(14), nullable=True, index=True)
    cpf = Column(String(11), nullable=True, index=True)
    id_estrangeiro = Column(String(20), nullable=True)
    nome = Column(String(150), nullable=False)
    ie = Column(String(30))
    email = Column(String(100))
    logradouro = Column(String(200))
    numero = Column(String(20))
    complemento = Column(String(100))
    bairro = Column(String(100))
    municipio = Column(String(100))
    uf = Column(String(2))
    cep = Column(String(8))
    fone = Column(String(20))
    autorizado = Column(Boolean, default=False, nullable=False)
    criado_em = Column(DateTime, default=_agora)
    atualizado_em = Column(DateTime, default=_agora, onupdate=_agora)

    notas = relationship("NotaFiscal", back_populates="destinatario_rel", foreign_keys="NotaFiscal.destinatario_id")


class Tributacao(Base):
    __tablename__ = "tributacoes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Chave de negócio: combinação CST/CSOSN + CFOP
    cst_icms = Column(String(3), nullable=False)
    cfop = Column(String(4), nullable=False)
    descricao = Column(String(200))
    aliq_icms = Column(Numeric(10, 4), default=0)
    aliq_pis = Column(Numeric(10, 4), default=0)
    aliq_cofins = Column(Numeric(10, 4), default=0)
    autorizado = Column(Boolean, default=False, nullable=False)
    criado_em = Column(DateTime, default=_agora)
    atualizado_em = Column(DateTime, default=_agora, onupdate=_agora)


class NotaFiscal(Base):
    __tablename__ = "notas_fiscais"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chave_acesso = Column(String(44), unique=True, nullable=False, index=True)
    numero_nf = Column(String(9))
    serie = Column(String(3))
    data_emissao = Column(String(30))
    natureza_operacao = Column(String(60))
    tipo_nf = Column(String(1))   # 0=entrada, 1=saída
    emitente_id = Column(Integer, ForeignKey("emitentes.id"))
    destinatario_id = Column(Integer, ForeignKey("destinatarios.id"))
    # Totais
    v_prod = Column(Numeric(15, 2), default=0)
    v_desc = Column(Numeric(15, 2), default=0)
    v_frete = Column(Numeric(15, 2), default=0)
    v_seg = Column(Numeric(15, 2), default=0)
    v_outro = Column(Numeric(15, 2), default=0)
    v_ipi = Column(Numeric(15, 2), default=0)
    v_pis = Column(Numeric(15, 2), default=0)
    v_cofins = Column(Numeric(15, 2), default=0)
    v_icms = Column(Numeric(15, 2), default=0)
    v_st = Column(Numeric(15, 2), default=0)
    v_nf = Column(Numeric(15, 2), default=0)
    # Validação
    validacao_ok = Column(Boolean, default=None, nullable=True)
    validacao_erros = Column(Text, default="")
    importado_em = Column(DateTime, default=_agora)

    emitente_rel = relationship("Emitente", back_populates="notas", foreign_keys=[emitente_id])
    destinatario_rel = relationship("Destinatario", back_populates="notas", foreign_keys=[destinatario_id])
    itens = relationship("ItemNota", back_populates="nota", cascade="all, delete-orphan")


class ItemNota(Base):
    __tablename__ = "itens_nota"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nota_id = Column(Integer, ForeignKey("notas_fiscais.id"), nullable=False)
    num_item = Column(Integer)
    codigo = Column(String(60))
    ean = Column(String(14))
    descricao = Column(String(200))
    ncm = Column(String(8))
    cfop = Column(String(4))
    unidade = Column(String(6))
    quantidade = Column(Numeric(15, 4), default=0)
    valor_unitario = Column(Numeric(15, 10), default=0)
    valor_bruto = Column(Numeric(15, 2), default=0)
    valor_desconto = Column(Numeric(15, 2), default=0)
    valor_total = Column(Numeric(15, 2), default=0)
    # Tributação do item
    icms_cst = Column(String(3))
    icms_orig = Column(String(1))
    icms_vbc = Column(Numeric(15, 2), default=0)
    icms_paliq = Column(Numeric(10, 4), default=0)
    icms_vicms = Column(Numeric(15, 2), default=0)
    ipi_cst = Column(String(2))
    ipi_vbc = Column(Numeric(15, 2), default=0)
    ipi_paliq = Column(Numeric(10, 4), default=0)
    ipi_vipi = Column(Numeric(15, 2), default=0)
    pis_cst = Column(String(2))
    pis_vbc = Column(Numeric(15, 2), default=0)
    pis_paliq = Column(Numeric(10, 4), default=0)
    pis_vpis = Column(Numeric(15, 2), default=0)
    cofins_cst = Column(String(2))
    cofins_vbc = Column(Numeric(15, 2), default=0)
    cofins_paliq = Column(Numeric(10, 4), default=0)
    cofins_vcofins = Column(Numeric(15, 2), default=0)

    nota = relationship("NotaFiscal", back_populates="itens")


# ---------------------------------------------------------------------------
# Criação das tabelas
# ---------------------------------------------------------------------------

def criar_tabelas():
    Base.metadata.create_all(bind=engine)


def get_db():
    """Gerador de sessão para uso com Flask."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
