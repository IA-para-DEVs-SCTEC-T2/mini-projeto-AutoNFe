"""
Agente 2 – Cadastro de Emitente, Destinatário e Tributação.
Verifica existência no banco e cadastra novos registros como pendentes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy.orm import Session

from src.agents.agent1_leitura import Emitente as EmitLeitura
from src.agents.agent1_leitura import Destinatario as DestLeitura
from src.agents.agent1_leitura import ResultadoLeitura
from src.database.models import (
    Emitente as EmitModel,
    Destinatario as DestModel,
    Tributacao as TribModel,
)


# ---------------------------------------------------------------------------
# Dataclasses de resultado
# ---------------------------------------------------------------------------

@dataclass
class StatusCadastro:
    entidade: str       # "Emitente" | "Destinatário" | "Tributação"
    identificador: str  # CNPJ/CPF ou "CST XX / CFOP XXXX"
    nome: str
    acao: str           # "encontrado" | "cadastrado"
    autorizado: bool
    id_banco: int


@dataclass
class ResultadoCadastro:
    emitente: Optional[StatusCadastro] = None
    destinatario: Optional[StatusCadastro] = None
    tributacoes: List[StatusCadastro] = field(default_factory=list)
    erros: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Agente 2 – classe principal
# ---------------------------------------------------------------------------

class AgenteCadastro:
    """
    Valida e cadastra Emitente, Destinatário e Tributações no banco SQLite.
    Novos registros são criados com autorizado=False (pendentes).
    """

    def __init__(self, db: Session):
        self._db = db

    def processar(self, resultado: ResultadoLeitura) -> ResultadoCadastro:
        """Ponto de entrada: processa todos os cadastros da NF-e."""
        rel = ResultadoCadastro()

        for nome_entidade, metodo, atributo in [
            ("emitente", self._processar_emitente, "emitente"),
            ("destinatário", self._processar_destinatario, "destinatario"),
        ]:
            try:
                setattr(rel, atributo, metodo(resultado))
            except Exception as exc:
                rel.erros.append(f"Erro ao processar {nome_entidade}: {exc}")

        try:
            rel.tributacoes = self._processar_tributacoes(resultado)
        except Exception as exc:
            rel.erros.append(f"Erro ao processar tributações: {exc}")

        return rel

    # ------------------------------------------------------------------
    # Emitente
    # ------------------------------------------------------------------

    def _processar_emitente(self, resultado: ResultadoLeitura) -> StatusCadastro:
        emit = resultado.emitente
        registro = self._buscar_emitente(emit)
        acao = "encontrado" if registro else "cadastrado"

        if not registro:
            registro = EmitModel(
                cnpj=emit.cnpj or None,
                cpf=emit.cpf or None,
                nome=emit.nome,
                fantasia=emit.fantasia,
                ie=emit.ie,
                crt=emit.crt,
                **_endereco_para_dict(emit),
                autorizado=False,
            )
            self._db.add(registro)
            self._db.flush()

        return StatusCadastro(
            entidade="Emitente",
            identificador=emit.cnpj or emit.cpf,
            nome=registro.nome,
            acao=acao,
            autorizado=registro.autorizado,
            id_banco=registro.id,
        )

    def _buscar_emitente(self, emit: EmitLeitura) -> Optional[EmitModel]:
        if emit.cnpj:
            return self._db.query(EmitModel).filter_by(cnpj=emit.cnpj).first()
        if emit.cpf:
            return self._db.query(EmitModel).filter_by(cpf=emit.cpf).first()
        return None

    # ------------------------------------------------------------------
    # Destinatário
    # ------------------------------------------------------------------

    def _processar_destinatario(self, resultado: ResultadoLeitura) -> StatusCadastro:
        dest = resultado.destinatario
        registro = self._buscar_destinatario(dest)
        acao = "encontrado" if registro else "cadastrado"

        if not registro:
            registro = DestModel(
                cnpj=dest.cnpj or None,
                cpf=dest.cpf or None,
                id_estrangeiro=dest.id_estrangeiro or None,
                nome=dest.nome,
                ie=dest.ie,
                email=dest.email,
                **_endereco_para_dict(dest),
                autorizado=False,
            )
            self._db.add(registro)
            self._db.flush()

        return StatusCadastro(
            entidade="Destinatário",
            identificador=dest.cnpj or dest.cpf or dest.id_estrangeiro,
            nome=registro.nome,
            acao=acao,
            autorizado=registro.autorizado,
            id_banco=registro.id,
        )

    def _buscar_destinatario(self, dest: DestLeitura) -> Optional[DestModel]:
        if dest.cnpj:
            return self._db.query(DestModel).filter_by(cnpj=dest.cnpj).first()
        if dest.cpf:
            return self._db.query(DestModel).filter_by(cpf=dest.cpf).first()
        return None

    # ------------------------------------------------------------------
    # Tributações
    # ------------------------------------------------------------------

    def _processar_tributacoes(self, resultado: ResultadoLeitura) -> List[StatusCadastro]:
        statuses: List[StatusCadastro] = []
        chaves_vistas: set = set()

        for produto in resultado.produtos:
            cst = produto.tributacao.icms_cst
            cfop = produto.cfop
            chave = (cst, cfop)

            if not cst or not cfop or chave in chaves_vistas:
                continue
            chaves_vistas.add(chave)

            registro = self._db.query(TribModel).filter_by(cst_icms=cst, cfop=cfop).first()
            acao = "encontrado" if registro else "cadastrado"

            if not registro:
                trib = produto.tributacao
                registro = TribModel(
                    cst_icms=cst,
                    cfop=cfop,
                    descricao=f"CST {cst} / CFOP {cfop}",
                    aliq_icms=float(trib.icms_paliq),
                    aliq_pis=float(trib.pis_paliq),
                    aliq_cofins=float(trib.cofins_paliq),
                    autorizado=False,
                )
                self._db.add(registro)
                self._db.flush()

            statuses.append(StatusCadastro(
                entidade="Tributação",
                identificador=f"CST {cst} / CFOP {cfop}",
                nome=registro.descricao,
                acao=acao,
                autorizado=registro.autorizado,
                id_banco=registro.id,
            ))

        return statuses


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _endereco_para_dict(entidade) -> dict:
    """Extrai campos de endereço de um Emitente ou Destinatário de leitura."""
    end = entidade.endereco
    return {
        "logradouro": end.logradouro,
        "numero": end.numero,
        "complemento": end.complemento,
        "bairro": end.bairro,
        "municipio": end.municipio,
        "uf": end.uf,
        "cep": end.cep,
        "fone": end.fone,
    }
