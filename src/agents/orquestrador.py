"""
Orquestrador – coordena Agente1 → Agente2 → Agente3 e persiste a NF-e.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy.orm import Session

from src.agents.agent1_leitura import AgenteLeitorNFe, ResultadoLeitura
from src.agents.agent2_cadastro import AgenteCadastro, ResultadoCadastro
from src.agents.agent3_validacao import AgenteValidacaoValores, ResultadoValidacao
from src.database.models import ItemNota, NotaFiscal


# ---------------------------------------------------------------------------
# Dataclass de resultado do processamento completo
# ---------------------------------------------------------------------------

@dataclass
class ResultadoProcessamento:
    leitura: Optional[ResultadoLeitura] = None
    cadastro: Optional[ResultadoCadastro] = None
    validacao: Optional[ResultadoValidacao] = None
    nota_id: Optional[int] = None
    erros: List[str] = field(default_factory=list)

    @property
    def sucesso(self) -> bool:
        return not self.erros and self.leitura is not None and not self.leitura.erros


# ---------------------------------------------------------------------------
# Orquestrador
# ---------------------------------------------------------------------------

class Orquestrador:
    """Coordena os três agentes e persiste os dados no banco."""

    def __init__(self, db: Session, validar_schema: bool = False):
        self._db = db
        self._agente_leitura = AgenteLeitorNFe(validar_schema=validar_schema)
        self._agente_cadastro = AgenteCadastro(db)
        self._agente_validacao = AgenteValidacaoValores()

    # ------------------------------------------------------------------
    # Pontos de entrada públicos
    # ------------------------------------------------------------------

    def processar_arquivo(self, caminho: str) -> ResultadoProcessamento:
        """Processa NF-e a partir de um caminho de arquivo."""
        return self._executar(self._agente_leitura.ler_arquivo(caminho))

    def processar_bytes(self, conteudo: bytes) -> ResultadoProcessamento:
        """Processa NF-e a partir de bytes XML."""
        return self._executar(self._agente_leitura.ler_bytes(conteudo))

    # ------------------------------------------------------------------
    # Pipeline interno
    # ------------------------------------------------------------------

    def _executar(self, leitura: ResultadoLeitura) -> ResultadoProcessamento:
        resultado = ResultadoProcessamento(leitura=leitura)

        if leitura.erros:
            resultado.erros.extend(leitura.erros)
            return resultado

        if self._nota_ja_importada(leitura.chave_acesso, resultado):
            return resultado

        resultado.cadastro = self._agente_cadastro.processar(leitura)
        resultado.erros.extend(resultado.cadastro.erros)

        resultado.validacao = self._agente_validacao.validar(leitura)

        self._persistir(leitura, resultado)
        return resultado

    def _nota_ja_importada(self, chave_acesso: str, resultado: ResultadoProcessamento) -> bool:
        existente = self._db.query(NotaFiscal).filter_by(chave_acesso=chave_acesso).first()
        if existente:
            resultado.nota_id = existente.id
            resultado.erros.append(f"NF-e já importada (chave: {chave_acesso[:10]}...)")
            return True
        return False

    def _persistir(self, leitura: ResultadoLeitura, resultado: ResultadoProcessamento) -> None:
        try:
            nota = self._criar_nota(leitura, resultado)
            self._criar_itens(nota.id, leitura)
            resultado.nota_id = nota.id
            self._db.commit()
        except Exception as exc:
            self._db.rollback()
            resultado.erros.append(f"Erro ao salvar NF-e: {exc}")

    # ------------------------------------------------------------------
    # Criação dos registros no banco
    # ------------------------------------------------------------------

    def _criar_nota(self, leitura: ResultadoLeitura, resultado: ResultadoProcessamento) -> NotaFiscal:
        cad = resultado.cadastro
        val = resultado.validacao
        t = leitura.totais

        nota = NotaFiscal(
            chave_acesso=leitura.chave_acesso,
            numero_nf=leitura.numero_nf,
            serie=leitura.serie,
            data_emissao=leitura.data_emissao,
            natureza_operacao=leitura.natureza_operacao,
            tipo_nf=leitura.tipo_nf,
            emitente_id=cad.emitente.id_banco if cad and cad.emitente else None,
            destinatario_id=cad.destinatario.id_banco if cad and cad.destinatario else None,
            v_prod=float(t.v_prod),
            v_desc=float(t.v_desc),
            v_frete=float(t.v_frete),
            v_seg=float(t.v_seg),
            v_outro=float(t.v_outro),
            v_ipi=float(t.v_ipi),
            v_pis=float(t.v_pis),
            v_cofins=float(t.v_cofins),
            v_icms=float(t.v_icms),
            v_st=float(t.v_st),
            v_nf=float(t.v_nf),
            validacao_ok=val.ok if val else None,
            validacao_erros=val.texto_divergencias() if val else "",
        )
        self._db.add(nota)
        self._db.flush()
        return nota

    def _criar_itens(self, nota_id: int, leitura: ResultadoLeitura) -> None:
        for produto in leitura.produtos:
            tr = produto.tributacao
            self._db.add(ItemNota(
                nota_id=nota_id,
                num_item=produto.num_item,
                codigo=produto.codigo,
                ean=produto.ean,
                descricao=produto.descricao,
                ncm=produto.ncm,
                cfop=produto.cfop,
                unidade=produto.unidade,
                quantidade=float(produto.quantidade),
                valor_unitario=float(produto.valor_unitario),
                valor_bruto=float(produto.valor_bruto),
                valor_desconto=float(produto.valor_desconto),
                valor_total=float(produto.valor_total),
                icms_cst=tr.icms_cst,
                icms_orig=tr.icms_orig,
                icms_vbc=float(tr.icms_vbc),
                icms_paliq=float(tr.icms_paliq),
                icms_vicms=float(tr.icms_vicms),
                ipi_cst=tr.ipi_cst,
                ipi_vbc=float(tr.ipi_vbc),
                ipi_paliq=float(tr.ipi_paliq),
                ipi_vipi=float(tr.ipi_vipi),
                pis_cst=tr.pis_cst,
                pis_vbc=float(tr.pis_vbc),
                pis_paliq=float(tr.pis_paliq),
                pis_vpis=float(tr.pis_vpis),
                cofins_cst=tr.cofins_cst,
                cofins_vbc=float(tr.cofins_vbc),
                cofins_paliq=float(tr.cofins_paliq),
                cofins_vcofins=float(tr.cofins_vcofins),
            ))


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _formatar_erros_validacao(val: Optional[ResultadoValidacao]) -> str:
    """Mantido por compatibilidade — use val.texto_divergencias() diretamente."""
    return val.texto_divergencias() if val else ""
