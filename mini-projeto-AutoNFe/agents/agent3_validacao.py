"""
Agente 3 – Validação de Valores.
Verifica Base × Alíquota por imposto e confere os totalizadores da NF-e.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple

from agents.agent1_leitura import Produto, ResultadoLeitura, Totais

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

TOLERANCIA = Decimal("0.02")   # margem de arredondamento aceita
_CEM = Decimal("100")

# ---------------------------------------------------------------------------
# Mensagens descritivas por campo — exibidas na tela de divergências
# ---------------------------------------------------------------------------

_DESCRICAO_CAMPO_ITEM = {
    "vProd-vDesc": "Valor do item (Qtd × Vl.Unit − Desconto) diverge do informado no XML",
    "vICMS":       "ICMS do item: Base × Alíquota diverge do vICMS informado no XML",
    "vIPI":        "IPI do item: Base × Alíquota diverge do vIPI informado no XML",
    "vPIS":        "PIS do item: Base × Alíquota diverge do vPIS informado no XML",
    "vCOFINS":     "COFINS do item: Base × Alíquota diverge do vCOFINS informado no XML",
}

_DESCRICAO_CAMPO_TOTAL = {
    "vProd":    "Total de Produtos (soma dos itens) diverge do vProd informado no totalizador",
    "vDesc":    "Total de Descontos (soma dos itens) diverge do vDesc informado no totalizador",
    "vICMS":    "Total de ICMS (soma dos itens) diverge do vICMS informado no totalizador",
    "vIPI":     "Total de IPI (soma dos itens) diverge do vIPI informado no totalizador",
    "vPIS":     "Total de PIS (soma dos itens) diverge do vPIS informado no totalizador",
    "vCOFINS":  "Total de COFINS (soma dos itens) diverge do vCOFINS informado no totalizador",
    "vNF":      (
        "Valor Total da NF-e diverge da fórmula oficial SEFAZ: "
        "vNF = vProd − vDesc + vFrete + vSeg + vOutro + vIPI − vICMSDeson"
    ),
}


def _label_total(campo_interno: str) -> str:
    """Retorna a mensagem descritiva para o campo de totalizador."""
    return _DESCRICAO_CAMPO_TOTAL.get(campo_interno, campo_interno)


def _label_item(campo_interno: str) -> str:
    """Retorna a mensagem descritiva para o campo de item."""
    return _DESCRICAO_CAMPO_ITEM.get(campo_interno, campo_interno)


# ---------------------------------------------------------------------------
# Dataclasses de resultado
# ---------------------------------------------------------------------------

@dataclass
class DiferencaItem:
    num_item: int
    descricao: str       # nome/descrição do produto ou "TOTAL"
    campo: str           # mensagem descritiva da divergência
    valor_xml: Decimal
    valor_calculado: Decimal
    diferenca: Decimal


@dataclass
class ResultadoValidacao:
    ok: bool = True
    diferencas_itens: List[DiferencaItem] = field(default_factory=list)
    diferencas_totais: List[DiferencaItem] = field(default_factory=list)
    erros: List[str] = field(default_factory=list)

    def resumo(self) -> str:
        if self.ok:
            return "✅ Todos os valores validados com sucesso."
        linhas = ["❌ Divergências encontradas:"]
        for d in self.diferencas_itens:
            linhas.append(
                f"  Item {d.num_item} ({d.descricao}): {d.campo} "
                f"| XML={d.valor_xml} | Calculado={d.valor_calculado} | Δ={d.diferenca}"
            )
        for d in self.diferencas_totais:
            linhas.append(
                f"  {d.campo} "
                f"| XML={d.valor_xml} | Calculado={d.valor_calculado} | Δ={d.diferenca}"
            )
        return "\n".join(linhas)

    def texto_divergencias(self) -> str:
        """Texto compacto para armazenar no banco (campo validacao_erros)."""
        partes = []
        for d in self.diferencas_itens:
            partes.append(f"Item {d.num_item}: {d.campo} (Δ R$ {d.diferenca})")
        for d in self.diferencas_totais:
            partes.append(f"{d.campo} (Δ R$ {d.diferenca})")
        return " | ".join(partes)


# ---------------------------------------------------------------------------
# Funções utilitárias (puras)
# ---------------------------------------------------------------------------

def _arredondar(valor, casas: int = 2) -> Decimal:
    """Arredonda para N casas decimais. Aceita int, float ou Decimal."""
    return Decimal(str(valor)).quantize(Decimal(10) ** -casas, rounding=ROUND_HALF_UP)


def _calcular_imposto(base: Decimal, aliquota: Decimal) -> Decimal:
    """Calcula imposto: base × alíquota / 100, arredondado a 2 casas."""
    return _arredondar(base * aliquota / _CEM)


def _verificar_divergencia(
    campo: str,
    num_item: int,
    descricao: str,
    valor_xml: Decimal,
    valor_calculado: Decimal,
    tolerancia: Decimal = TOLERANCIA,
) -> Optional[DiferencaItem]:
    """Retorna DiferencaItem com mensagem descritiva se exceder a tolerância."""
    diferenca = abs(_arredondar(valor_xml) - _arredondar(valor_calculado))
    if diferenca <= tolerancia:
        return None
    return DiferencaItem(
        num_item=num_item,
        descricao=descricao,
        campo=campo,
        valor_xml=_arredondar(valor_xml),
        valor_calculado=_arredondar(valor_calculado),
        diferenca=diferenca,
    )


# ---------------------------------------------------------------------------
# Agente 3 – classe principal
# ---------------------------------------------------------------------------

class AgenteValidacaoValores:
    """Valida Base × Alíquota e totalizadores da NF-e."""

    def validar(self, resultado: ResultadoLeitura) -> ResultadoValidacao:
        rel = ResultadoValidacao()

        for produto in resultado.produtos:
            self._validar_item(produto, rel)

        self._validar_totais(resultado.totais, resultado.produtos, rel)

        rel.ok = not rel.diferencas_itens and not rel.diferencas_totais and not rel.erros
        return rel

    # ------------------------------------------------------------------
    # Validação por item
    # ------------------------------------------------------------------

    def _validar_item(self, produto: Produto, rel: ResultadoValidacao) -> None:
        t = produto.tributacao
        n, desc = produto.num_item, produto.descricao

        # Valor total: quantidade × unitário − desconto
        calc_total = (
            _arredondar(produto.quantidade * produto.valor_unitario)
            - produto.valor_desconto
        )
        self._registrar_item(
            rel.diferencas_itens, "vProd-vDesc", n, desc,
            produto.valor_total, calc_total,
        )

        # Impostos: Base × Alíquota / 100
        impostos: List[Tuple[str, Decimal, Decimal, Decimal]] = [
            ("vICMS",   t.icms_vbc,   t.icms_paliq,   t.icms_vicms),
            ("vIPI",    t.ipi_vbc,    t.ipi_paliq,    t.ipi_vipi),
            ("vPIS",    t.pis_vbc,    t.pis_paliq,    t.pis_vpis),
            ("vCOFINS", t.cofins_vbc, t.cofins_paliq, t.cofins_vcofins),
        ]
        for campo, base, aliq, valor_xml in impostos:
            if base > 0 and aliq > 0:
                self._registrar_item(
                    rel.diferencas_itens, campo, n, desc,
                    valor_xml, _calcular_imposto(base, aliq),
                )

    # ------------------------------------------------------------------
    # Validação dos totalizadores
    # ------------------------------------------------------------------

    def _validar_totais(
        self, totais: Totais, produtos: List[Produto], rel: ResultadoValidacao
    ) -> None:
        # Tolerância dinâmica: R$ 0,02 base + R$ 0,01 por item (arredondamento acumulado)
        tol = TOLERANCIA + Decimal("0.01") * len(produtos)

        checks: List[Tuple[str, Decimal, Decimal]] = [
            ("vProd",   totais.v_prod,   sum(p.valor_bruto              for p in produtos)),
            ("vDesc",   totais.v_desc,   sum(p.valor_desconto           for p in produtos)),
            ("vICMS",   totais.v_icms,   sum(p.tributacao.icms_vicms    for p in produtos)),
            ("vIPI",    totais.v_ipi,    sum(p.tributacao.ipi_vipi      for p in produtos)),
            ("vPIS",    totais.v_pis,    sum(p.tributacao.pis_vpis      for p in produtos)),
            ("vCOFINS", totais.v_cofins, sum(p.tributacao.cofins_vcofins for p in produtos)),
        ]
        for campo_interno, xml_val, calc_val in checks:
            diferenca = abs(_arredondar(xml_val) - _arredondar(calc_val))
            if diferenca > tol:
                rel.diferencas_totais.append(DiferencaItem(
                    num_item=0,
                    descricao="TOTAL",
                    campo=_label_total(campo_interno),
                    valor_xml=_arredondar(xml_val),
                    valor_calculado=_arredondar(calc_val),
                    diferenca=diferenca,
                ))

        # vNF = vProd − vDesc + vFrete + vSeg + vOutro + vIPI − vICMSDeson
        calc_nf = _arredondar(
            totais.v_prod - totais.v_desc
            + totais.v_frete + totais.v_seg + totais.v_outro
            + totais.v_ipi - totais.v_icms_deson
        )
        div = _verificar_divergencia(
            _label_total("vNF"), 0, "TOTAL", totais.v_nf, calc_nf
        )
        if div:
            rel.diferencas_totais.append(div)

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    @staticmethod
    def _registrar_item(
        lista: List[DiferencaItem],
        campo_interno: str,
        num_item: int,
        descricao: str,
        valor_xml: Decimal,
        valor_calculado: Decimal,
    ) -> None:
        """Adiciona divergência de item com mensagem descritiva."""
        div = _verificar_divergencia(
            _label_item(campo_interno), num_item, descricao,
            valor_xml, valor_calculado,
        )
        if div:
            lista.append(div)
