"""
Agente 2 — Cadastro de Emitente, Destinatário e Tributação

Recebe os dados extraídos pelo Agente 1 e realiza verificação e cadastro
no banco de dados local.

SEGURANÇA — SQL Injection:
- TODAS as queries usam parâmetros posicionais (?) do sqlite3.
- Nenhuma query é construída por concatenação de string ou f-string.
- Dados do XML são tratados como entrada não confiável.

SEGURANÇA — Sanitização de dados:
- Todos os campos de texto extraídos do XML passam por _sanitizar_texto()
  antes de serem gravados no banco.
- Campos numéricos (CNPJ, CPF, alíquota) são normalizados para dígitos/ponto.
- Comprimento máximo é aplicado por campo para evitar dados anômalos.
"""

import re
import sqlite3
from database.conexao import obter_conexao


# ---------------------------------------------------------------------------
# Sanitização
# ---------------------------------------------------------------------------

# Comprimentos máximos por campo (baseados no leiaute NF-e v4.00)
_MAX_LEN = {
    "cnpj": 14,
    "cpf": 11,
    "razao_social": 60,
    "ie": 14,
    "logradouro": 60,
    "municipio": 60,
    "uf": 2,
    "cep": 8,
    "cfop": 4,
    "cst_csosn": 3,
    "aliquota": 7,
    "default": 255,
}


def _sanitizar_texto(valor: str, campo: str = "default") -> str:
    """
    Sanitiza um campo de texto vindo do XML antes de gravar no banco.

    Operações aplicadas:
    - Remove caracteres de controle (exceto espaço normal)
    - Faz strip de espaços nas bordas
    - Trunca no comprimento máximo definido para o campo

    Args:
        valor:  String a sanitizar.
        campo:  Nome do campo para aplicar o limite correto.

    Returns:
        String sanitizada.
    """
    if not isinstance(valor, str):
        return ""
    # Remove caracteres de controle (U+0000–U+001F e U+007F), exceto \t e \n
    valor = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", valor)
    valor = valor.strip()
    limite = _MAX_LEN.get(campo, _MAX_LEN["default"])
    return valor[:limite]


def _sanitizar_somente_digitos(valor: str, campo: str) -> str:
    """Remove tudo que não for dígito e trunca no limite do campo."""
    apenas_digitos = re.sub(r"\D", "", valor or "")
    limite = _MAX_LEN.get(campo, _MAX_LEN["default"])
    return apenas_digitos[:limite]


def _sanitizar_numerico(valor: str, campo: str = "aliquota") -> str:
    """Mantém apenas dígitos e ponto decimal; trunca no limite do campo."""
    normalizado = re.sub(r"[^\d.]", "", valor or "")
    limite = _MAX_LEN.get(campo, _MAX_LEN["default"])
    return normalizado[:limite]


def _sanitizar_emitente(dados: dict) -> dict:
    return {
        "cnpj": _sanitizar_somente_digitos(dados.get("cnpj", ""), "cnpj"),
        "razao_social": _sanitizar_texto(dados.get("razao_social", ""), "razao_social"),
        "ie": _sanitizar_somente_digitos(dados.get("ie", ""), "ie"),
    }


def _sanitizar_destinatario(dados: dict) -> dict:
    return {
        "cnpj": _sanitizar_somente_digitos(dados.get("cnpj", ""), "cnpj"),
        "cpf": _sanitizar_somente_digitos(dados.get("cpf", ""), "cpf"),
        "razao_social": _sanitizar_texto(dados.get("razao_social", ""), "razao_social"),
        "ie": _sanitizar_somente_digitos(dados.get("ie", ""), "ie"),
    }


# ---------------------------------------------------------------------------
# Emitente
# ---------------------------------------------------------------------------

def buscar_emitente_por_cnpj(cnpj: str) -> sqlite3.Row | None:
    """
    Busca um emitente pelo CNPJ.

    Usa parâmetro posicional (?) — nunca concatenação de string.

    Args:
        cnpj: CNPJ do emitente (somente dígitos).

    Returns:
        Row do emitente ou None se não encontrado.
    """
    with obter_conexao() as conn:
        return conn.execute(
            "SELECT * FROM emitente WHERE cnpj = ?",
            (cnpj,),
        ).fetchone()


def cadastrar_emitente(dados: dict) -> int:
    """
    Cadastra um novo emitente com status PENDENTE.

    Args:
        dados: Dicionário com cnpj, razao_social e ie.

    Returns:
        ID do registro inserido.
    """
    with obter_conexao() as conn:
        cursor = conn.execute(
            """
            INSERT INTO emitente (cnpj, razao_social, ie, status)
            VALUES (?, ?, ?, 'PENDENTE')
            """,
            (
                dados.get("cnpj", ""),
                dados.get("razao_social", ""),
                dados.get("ie", ""),
            ),
        )
        return cursor.lastrowid


def processar_emitente(dados_emitente: dict) -> dict:
    """
    Verifica se o emitente existe; cadastra se não existir.

    Sanitiza os dados antes de qualquer operação no banco.

    Args:
        dados_emitente: Dados extraídos pelo Agente 1.

    Returns:
        Dicionário com 'id', 'status' e 'acao' ('encontrado' | 'cadastrado').
    """
    dados_limpos = _sanitizar_emitente(dados_emitente)
    cnpj = dados_limpos["cnpj"]
    registro = buscar_emitente_por_cnpj(cnpj)

    if registro:
        return {"id": registro["id"], "status": registro["status"], "acao": "encontrado"}

    novo_id = cadastrar_emitente(dados_limpos)
    return {"id": novo_id, "status": "PENDENTE", "acao": "cadastrado"}


# ---------------------------------------------------------------------------
# Destinatário
# ---------------------------------------------------------------------------

def buscar_destinatario(cnpj: str = "", cpf: str = "") -> sqlite3.Row | None:
    """
    Busca um destinatário por CNPJ ou CPF.

    Usa parâmetros posicionais — sem concatenação de string.

    Args:
        cnpj: CNPJ do destinatário (use "" se não aplicável).
        cpf:  CPF do destinatário (use "" se não aplicável).

    Returns:
        Row do destinatário ou None se não encontrado.
    """
    with obter_conexao() as conn:
        if cnpj:
            return conn.execute(
                "SELECT * FROM destinatario WHERE cnpj = ?",
                (cnpj,),
            ).fetchone()
        if cpf:
            return conn.execute(
                "SELECT * FROM destinatario WHERE cpf = ?",
                (cpf,),
            ).fetchone()
    return None


def cadastrar_destinatario(dados: dict) -> int:
    """
    Cadastra um novo destinatário com status PENDENTE.

    Args:
        dados: Dicionário com cnpj, cpf, razao_social e ie.

    Returns:
        ID do registro inserido.
    """
    with obter_conexao() as conn:
        cursor = conn.execute(
            """
            INSERT INTO destinatario (cnpj, cpf, razao_social, ie, status)
            VALUES (?, ?, ?, ?, 'PENDENTE')
            """,
            (
                dados.get("cnpj", "") or None,
                dados.get("cpf", "") or None,
                dados.get("razao_social", ""),
                dados.get("ie", ""),
            ),
        )
        return cursor.lastrowid


def processar_destinatario(dados_destinatario: dict) -> dict:
    """
    Verifica se o destinatário existe; cadastra se não existir.

    Sanitiza os dados antes de qualquer operação no banco.

    Args:
        dados_destinatario: Dados extraídos pelo Agente 1.

    Returns:
        Dicionário com 'id', 'status' e 'acao'.
    """
    dados_limpos = _sanitizar_destinatario(dados_destinatario)
    cnpj = dados_limpos["cnpj"]
    cpf = dados_limpos["cpf"]
    registro = buscar_destinatario(cnpj=cnpj, cpf=cpf)

    if registro:
        return {"id": registro["id"], "status": registro["status"], "acao": "encontrado"}

    novo_id = cadastrar_destinatario(dados_limpos)
    return {"id": novo_id, "status": "PENDENTE", "acao": "cadastrado"}


# ---------------------------------------------------------------------------
# Tributação
# ---------------------------------------------------------------------------

def buscar_tributacao(cfop: str, cst_csosn: str, aliquota: str) -> sqlite3.Row | None:
    """
    Busca uma tributação pela combinação CFOP + CST/CSOSN + alíquota.

    Usa três parâmetros posicionais — sem concatenação de string.

    Args:
        cfop:      Código Fiscal de Operações e Prestações.
        cst_csosn: Código de Situação Tributária ou CSOSN.
        aliquota:  Alíquota aplicada.

    Returns:
        Row da tributação ou None se não encontrada.
    """
    with obter_conexao() as conn:
        return conn.execute(
            """
            SELECT * FROM tributacao
            WHERE cfop = ? AND cst_csosn = ? AND aliquota = ?
            """,
            (cfop, cst_csosn, aliquota),
        ).fetchone()


def cadastrar_tributacao(cfop: str, cst_csosn: str, aliquota: str) -> int:
    """
    Cadastra uma nova tributação com status PENDENTE.

    Args:
        cfop:      CFOP da operação.
        cst_csosn: CST ou CSOSN.
        aliquota:  Alíquota.

    Returns:
        ID do registro inserido.
    """
    with obter_conexao() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tributacao (cfop, cst_csosn, aliquota, status)
            VALUES (?, ?, ?, 'PENDENTE')
            """,
            (cfop, cst_csosn, aliquota),
        )
        return cursor.lastrowid


def processar_tributacao(dados_tributacao: list[dict]) -> list[dict]:
    """
    Processa a lista de tributações extraídas pelo Agente 1.

    Sanitiza cfop, cst e alíquota antes de consultar ou gravar no banco.

    Args:
        dados_tributacao: Lista de dicionários com cfop, icms, pis, cofins.

    Returns:
        Lista de resultados com 'cfop', 'id', 'status' e 'acao'.
    """
    resultados = []

    for item in dados_tributacao:
        cfop = _sanitizar_somente_digitos(item.get("cfop", ""), "cfop")
        icms = item.get("icms", {})
        cst = _sanitizar_texto(icms.get("cst", ""), "cst_csosn")
        aliquota = _sanitizar_numerico(icms.get("aliquota", ""), "aliquota")

        registro = buscar_tributacao(cfop, cst, aliquota)

        if registro:
            resultados.append({
                "cfop": cfop,
                "id": registro["id"],
                "status": registro["status"],
                "acao": "encontrado",
            })
        else:
            novo_id = cadastrar_tributacao(cfop, cst, aliquota)
            resultados.append({
                "cfop": cfop,
                "id": novo_id,
                "status": "PENDENTE",
                "acao": "cadastrado",
            })

    return resultados


# ---------------------------------------------------------------------------
# Ponto de entrada do Agente 2
# ---------------------------------------------------------------------------

def processar(dados_nfe: dict) -> dict:
    """
    Ponto de entrada do Agente 2.

    Recebe o dicionário completo extraído pelo Agente 1 e processa
    emitente, destinatário e tributações.

    Args:
        dados_nfe: Saída de agente1_leitura.extrair_dados_nfe().

    Returns:
        Dicionário com os resultados de cada processamento.
    """
    return {
        "emitente": processar_emitente(dados_nfe.get("emitente", {})),
        "destinatario": processar_destinatario(dados_nfe.get("destinatario", {})),
        "tributacao": processar_tributacao(dados_nfe.get("tributacao", [])),
    }
