"""
Serializers – converte modelos ORM em dicionários para as respostas JSON.
Elimina a serialização inline repetida nas rotas Flask.
"""

from __future__ import annotations

from typing import Any

from database.models import Destinatario, Emitente, ItemNota, NotaFiscal, Tributacao


def _fmt_data(dt, fmt: str = "%d/%m/%Y") -> str:
    return dt.strftime(fmt) if dt else ""


def _float(valor) -> float:
    return float(valor or 0)


# ---------------------------------------------------------------------------
# Emitente
# ---------------------------------------------------------------------------

def serializar_emitente(e: Emitente) -> dict[str, Any]:
    return {
        "id": e.id,
        "cnpj": e.cnpj,
        "cpf": e.cpf,
        "nome": e.nome,
        "fantasia": e.fantasia,
        "municipio": e.municipio,
        "uf": e.uf,
        "autorizado": e.autorizado,
        "criado_em": _fmt_data(e.criado_em),
    }


def serializar_emitente_detalhe(e: Emitente) -> dict[str, Any]:
    return {
        "id": e.id,
        "cnpj": e.cnpj,
        "cpf": e.cpf,
        "nome": e.nome,
        "fantasia": e.fantasia,
        "ie": e.ie,
        "crt": e.crt,
        "logradouro": e.logradouro,
        "numero": e.numero,
        "complemento": e.complemento,
        "bairro": e.bairro,
        "municipio": e.municipio,
        "uf": e.uf,
        "cep": e.cep,
        "fone": e.fone,
        "autorizado": e.autorizado,
        "criado_em": _fmt_data(e.criado_em),
        "total_notas": len(e.notas) if e.notas else 0,
    }


def serializar_emitente_resumo(e: Emitente | None) -> dict[str, Any]:
    if not e:
        return {"nome": "", "cnpj": "", "municipio": "", "uf": ""}
    return {
        "nome": e.nome,
        "cnpj": e.cnpj,
        "municipio": e.municipio,
        "uf": e.uf,
    }


# ---------------------------------------------------------------------------
# Destinatário
# ---------------------------------------------------------------------------

def serializar_destinatario(d: Destinatario) -> dict[str, Any]:
    return {
        "id": d.id,
        "cnpj": d.cnpj,
        "cpf": d.cpf,
        "nome": d.nome,
        "municipio": d.municipio,
        "uf": d.uf,
        "autorizado": d.autorizado,
        "criado_em": _fmt_data(d.criado_em),
    }


def serializar_destinatario_detalhe(d: Destinatario) -> dict[str, Any]:
    return {
        "id": d.id,
        "cnpj": d.cnpj,
        "cpf": d.cpf,
        "id_estrangeiro": d.id_estrangeiro,
        "nome": d.nome,
        "ie": d.ie,
        "email": d.email,
        "logradouro": d.logradouro,
        "numero": d.numero,
        "complemento": d.complemento,
        "bairro": d.bairro,
        "municipio": d.municipio,
        "uf": d.uf,
        "cep": d.cep,
        "fone": d.fone,
        "autorizado": d.autorizado,
        "criado_em": _fmt_data(d.criado_em),
        "total_notas": len(d.notas) if d.notas else 0,
    }


def serializar_destinatario_resumo(d: Destinatario | None) -> dict[str, Any]:
    if not d:
        return {"nome": "", "cnpj": "", "municipio": "", "uf": ""}
    return {
        "nome": d.nome,
        "cnpj": d.cnpj,
        "municipio": d.municipio,
        "uf": d.uf,
    }


# ---------------------------------------------------------------------------
# Tributação
# ---------------------------------------------------------------------------

def serializar_tributacao(t: Tributacao) -> dict[str, Any]:
    return {
        "id": t.id,
        "cst_icms": t.cst_icms,
        "cfop": t.cfop,
        "descricao": t.descricao,
        "aliq_icms": _float(t.aliq_icms),
        "aliq_pis": _float(t.aliq_pis),
        "aliq_cofins": _float(t.aliq_cofins),
        "autorizado": t.autorizado,
        "criado_em": _fmt_data(t.criado_em),
    }


# ---------------------------------------------------------------------------
# Item de NF-e
# ---------------------------------------------------------------------------

def serializar_item(i: ItemNota) -> dict[str, Any]:
    return {
        "num_item": i.num_item,
        "codigo": i.codigo,
        "descricao": i.descricao,
        "ncm": i.ncm,
        "cfop": i.cfop,
        "unidade": i.unidade,
        "quantidade": _float(i.quantidade),
        "valor_unitario": _float(i.valor_unitario),
        "valor_bruto": _float(i.valor_bruto),
        "valor_desconto": _float(i.valor_desconto),
        "valor_total": _float(i.valor_total),
        "icms_cst": i.icms_cst,
        "icms_paliq": _float(i.icms_paliq),
        "icms_vicms": _float(i.icms_vicms),
        "ipi_vipi": _float(i.ipi_vipi),
        "pis_vpis": _float(i.pis_vpis),
        "cofins_vcofins": _float(i.cofins_vcofins),
    }


# ---------------------------------------------------------------------------
# NF-e (listagem)
# ---------------------------------------------------------------------------

def serializar_nota_resumo(n: NotaFiscal) -> dict[str, Any]:
    return {
        "id": n.id,
        "chave_acesso": n.chave_acesso,
        "numero_nf": n.numero_nf,
        "serie": n.serie,
        "data_emissao": n.data_emissao,
        "natureza_operacao": n.natureza_operacao,
        "tipo_nf": n.tipo_nf,
        "emitente": n.emitente_rel.nome if n.emitente_rel else "",
        "destinatario": n.destinatario_rel.nome if n.destinatario_rel else "",
        "v_nf": _float(n.v_nf),
        "validacao_ok": n.validacao_ok,
        "validacao_erros": n.validacao_erros,
        "importado_em": _fmt_data(n.importado_em, "%d/%m/%Y %H:%M"),
    }


def serializar_nota_detalhe(n: NotaFiscal) -> dict[str, Any]:
    return {
        **serializar_nota_resumo(n),
        "emitente": serializar_emitente_resumo(n.emitente_rel),
        "destinatario": serializar_destinatario_resumo(n.destinatario_rel),
        "totais": {
            "v_prod": _float(n.v_prod),
            "v_desc": _float(n.v_desc),
            "v_frete": _float(n.v_frete),
            "v_seg": _float(n.v_seg),
            "v_outro": _float(n.v_outro),
            "v_ipi": _float(n.v_ipi),
            "v_pis": _float(n.v_pis),
            "v_cofins": _float(n.v_cofins),
            "v_icms": _float(n.v_icms),
            "v_st": _float(n.v_st),
            "v_nf": _float(n.v_nf),
        },
        "itens": [serializar_item(i) for i in n.itens],
    }


# ---------------------------------------------------------------------------
# Dashboard – nota resumida para últimas importações
# ---------------------------------------------------------------------------

def serializar_nota_dashboard(n: NotaFiscal) -> dict[str, Any]:
    return {
        "id": n.id,
        "numero_nf": n.numero_nf,
        "serie": n.serie,
        "data_emissao": n.data_emissao,
        "emitente": n.emitente_rel.nome if n.emitente_rel else "",
        "v_nf": _float(n.v_nf),
        "validacao_ok": n.validacao_ok,
        "importado_em": _fmt_data(n.importado_em, "%d/%m/%Y %H:%M"),
    }
