"""
Repository – camada de acesso a dados.
Centraliza todas as queries, eliminando duplicação nas rotas Flask.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Generator, List, Optional, Type

from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import (
    Destinatario,
    Emitente,
    ItemNota,
    NotaFiscal,
    SessionLocal,
    Tributacao,
)

# ---------------------------------------------------------------------------
# Tipos auxiliares
# ---------------------------------------------------------------------------

_FILTRO_STATUS = {"pendentes": False, "autorizados": True}


# ---------------------------------------------------------------------------
# Context manager de sessão
# ---------------------------------------------------------------------------

@contextmanager
def sessao_db() -> Generator[Session, None, None]:
    """Abre uma sessão e garante fechamento mesmo em caso de exceção."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Helpers genéricos
# ---------------------------------------------------------------------------

def _aplicar_filtro_status(query, modelo, status: str):
    """Aplica filtro de autorização quando status não for 'todos'."""
    if status in _FILTRO_STATUS:
        return query.filter_by(autorizado=_FILTRO_STATUS[status])
    return query


def _contar_por_status(db: Session, modelo) -> dict:
    """Retorna contagem de registros autorizados e pendentes."""
    return {
        "autorizados": db.query(func.count(modelo.id)).filter_by(autorizado=True).scalar(),
        "pendentes": db.query(func.count(modelo.id)).filter_by(autorizado=False).scalar(),
    }


def _autorizar_por_ids(db: Session, modelo, ids: List[int]) -> int:
    """Autoriza registros pelos IDs fornecidos. Retorna quantidade atualizada."""
    atualizados = (
        db.query(modelo)
        .filter(modelo.id.in_(ids))
        .update({"autorizado": True}, synchronize_session=False)
    )
    db.commit()
    return atualizados


# ---------------------------------------------------------------------------
# NF-e
# ---------------------------------------------------------------------------

def buscar_nota_por_chave(db: Session, chave_acesso: str) -> Optional[NotaFiscal]:
    return db.query(NotaFiscal).filter_by(chave_acesso=chave_acesso).first()


def buscar_nota_por_id(db: Session, nota_id: int) -> Optional[NotaFiscal]:
    return db.query(NotaFiscal).filter_by(id=nota_id).first()


def listar_notas(db: Session) -> List[NotaFiscal]:
    return db.query(NotaFiscal).order_by(NotaFiscal.importado_em.desc()).all()


def contar_notas_desde(db: Session, data_inicio: datetime) -> int:
    return (
        db.query(func.count(NotaFiscal.id))
        .filter(NotaFiscal.importado_em >= data_inicio)
        .scalar()
    )


def ultimas_notas(db: Session, limite: int = 5) -> List[NotaFiscal]:
    return (
        db.query(NotaFiscal)
        .order_by(NotaFiscal.importado_em.desc())
        .limit(limite)
        .all()
    )


# ---------------------------------------------------------------------------
# Emitentes
# ---------------------------------------------------------------------------

def listar_emitentes(db: Session, status: str = "todos") -> List[Emitente]:
    query = db.query(Emitente)
    query = _aplicar_filtro_status(query, Emitente, status)
    return query.order_by(Emitente.nome).all()


def buscar_emitente_por_id(db: Session, emitente_id: int) -> Optional[Emitente]:
    return db.query(Emitente).filter_by(id=emitente_id).first()


def contar_emitentes(db: Session) -> dict:
    return _contar_por_status(db, Emitente)


def autorizar_emitentes(db: Session, ids: List[int]) -> int:
    return _autorizar_por_ids(db, Emitente, ids)


# ---------------------------------------------------------------------------
# Destinatários
# ---------------------------------------------------------------------------

def listar_destinatarios(db: Session, status: str = "todos") -> List[Destinatario]:
    query = db.query(Destinatario)
    query = _aplicar_filtro_status(query, Destinatario, status)
    return query.order_by(Destinatario.nome).all()


def buscar_destinatario_por_id(db: Session, destinatario_id: int) -> Optional[Destinatario]:
    return db.query(Destinatario).filter_by(id=destinatario_id).first()


def contar_destinatarios(db: Session) -> dict:
    return _contar_por_status(db, Destinatario)


def autorizar_destinatarios(db: Session, ids: List[int]) -> int:
    return _autorizar_por_ids(db, Destinatario, ids)


# ---------------------------------------------------------------------------
# Tributações
# ---------------------------------------------------------------------------

def listar_tributacoes(db: Session, status: str = "todos") -> List[Tributacao]:
    query = db.query(Tributacao)
    query = _aplicar_filtro_status(query, Tributacao, status)
    return query.order_by(Tributacao.cfop, Tributacao.cst_icms).all()


def contar_tributacoes(db: Session) -> dict:
    return _contar_por_status(db, Tributacao)


def autorizar_tributacoes(db: Session, ids: List[int]) -> int:
    return _autorizar_por_ids(db, Tributacao, ids)
