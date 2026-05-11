"""
Agente 1 – Leitura de NF-e (XML)
Extrai emitente, destinatário, produtos, tributação e totalizadores
de arquivos NF-e v4.00 usando o schema leiauteNFe_v4.00.xsd.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from lxml import etree

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

NFE_NAMESPACE = "http://www.portalfiscal.inf.br/nfe"
NS = {"nfe": NFE_NAMESPACE}

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XSD_PATH = os.path.join(_BASE_DIR, "data", "schemas", "leiauteNFe_v4.00.xsd")

_CEM = Decimal("100")


# ---------------------------------------------------------------------------
# Dataclasses de domínio
# ---------------------------------------------------------------------------

@dataclass
class Endereco:
    logradouro: str = ""
    numero: str = ""
    complemento: str = ""
    bairro: str = ""
    municipio: str = ""
    uf: str = ""
    cep: str = ""
    pais: str = ""
    fone: str = ""


@dataclass
class Emitente:
    cnpj: str = ""
    cpf: str = ""
    nome: str = ""
    fantasia: str = ""
    ie: str = ""
    crt: str = ""
    endereco: Endereco = field(default_factory=Endereco)


@dataclass
class Destinatario:
    cnpj: str = ""
    cpf: str = ""
    id_estrangeiro: str = ""
    nome: str = ""
    ie: str = ""
    email: str = ""
    endereco: Endereco = field(default_factory=Endereco)


@dataclass
class TributacaoItem:
    icms_cst: str = ""
    icms_orig: str = ""
    icms_modbc: str = ""
    icms_vbc: Decimal = Decimal("0")
    icms_paliq: Decimal = Decimal("0")
    icms_vicms: Decimal = Decimal("0")
    icms_credpres: Decimal = Decimal("0")
    ipi_cst: str = ""
    ipi_vbc: Decimal = Decimal("0")
    ipi_paliq: Decimal = Decimal("0")
    ipi_vipi: Decimal = Decimal("0")
    pis_cst: str = ""
    pis_vbc: Decimal = Decimal("0")
    pis_paliq: Decimal = Decimal("0")
    pis_vpis: Decimal = Decimal("0")
    cofins_cst: str = ""
    cofins_vbc: Decimal = Decimal("0")
    cofins_paliq: Decimal = Decimal("0")
    cofins_vcofins: Decimal = Decimal("0")


@dataclass
class Produto:
    num_item: int = 0
    codigo: str = ""
    ean: str = ""
    descricao: str = ""
    ncm: str = ""
    cfop: str = ""
    unidade: str = ""
    quantidade: Decimal = Decimal("0")
    valor_unitario: Decimal = Decimal("0")
    valor_bruto: Decimal = Decimal("0")
    valor_desconto: Decimal = Decimal("0")
    valor_total: Decimal = Decimal("0")
    tributacao: TributacaoItem = field(default_factory=TributacaoItem)


@dataclass
class Totais:
    v_bc: Decimal = Decimal("0")
    v_icms: Decimal = Decimal("0")
    v_icms_deson: Decimal = Decimal("0")
    v_fcp: Decimal = Decimal("0")
    v_bcsT: Decimal = Decimal("0")
    v_st: Decimal = Decimal("0")
    v_prod: Decimal = Decimal("0")
    v_frete: Decimal = Decimal("0")
    v_seg: Decimal = Decimal("0")
    v_desc: Decimal = Decimal("0")
    v_ipi: Decimal = Decimal("0")
    v_pis: Decimal = Decimal("0")
    v_cofins: Decimal = Decimal("0")
    v_outro: Decimal = Decimal("0")
    v_nf: Decimal = Decimal("0")


@dataclass
class ResultadoLeitura:
    chave_acesso: str = ""
    numero_nf: str = ""
    serie: str = ""
    data_emissao: str = ""
    natureza_operacao: str = ""
    tipo_nf: str = ""
    emitente: Emitente = field(default_factory=Emitente)
    destinatario: Destinatario = field(default_factory=Destinatario)
    produtos: List[Produto] = field(default_factory=list)
    totais: Totais = field(default_factory=Totais)
    erros: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Funções utilitárias de parsing (puras, sem efeitos colaterais)
# ---------------------------------------------------------------------------

def _to_decimal(valor: Optional[str]) -> Decimal:
    """Converte string para Decimal; retorna zero em caso de falha."""
    if not valor:
        return Decimal("0")
    try:
        return Decimal(valor.strip())
    except InvalidOperation:
        return Decimal("0")


def _texto(elemento, xpath: str) -> str:
    """Extrai o texto do primeiro nó encontrado pelo XPath com namespace NFe."""
    nos = elemento.xpath(xpath, namespaces=NS)
    return (nos[0].text or "").strip() if nos else ""


def _primeiro_no(elemento, xpath: str):
    """Retorna o primeiro nó encontrado ou None."""
    nos = elemento.xpath(xpath, namespaces=NS)
    return nos[0] if nos else None


# ---------------------------------------------------------------------------
# Parsers de seções do XML
# ---------------------------------------------------------------------------

def _parse_endereco(elem) -> Endereco:
    return Endereco(
        logradouro=_texto(elem, "nfe:xLgr"),
        numero=_texto(elem, "nfe:nro"),
        complemento=_texto(elem, "nfe:xCpl"),
        bairro=_texto(elem, "nfe:xBairro"),
        municipio=_texto(elem, "nfe:xMun"),
        uf=_texto(elem, "nfe:UF"),
        cep=_texto(elem, "nfe:CEP"),
        pais=_texto(elem, "nfe:xPais"),
        fone=_texto(elem, "nfe:fone"),
    )


def _parse_emitente(emit_elem) -> Emitente:
    end_node = _primeiro_no(emit_elem, "nfe:enderEmit")
    return Emitente(
        cnpj=_texto(emit_elem, "nfe:CNPJ"),
        cpf=_texto(emit_elem, "nfe:CPF"),
        nome=_texto(emit_elem, "nfe:xNome"),
        fantasia=_texto(emit_elem, "nfe:xFant"),
        ie=_texto(emit_elem, "nfe:IE"),
        crt=_texto(emit_elem, "nfe:CRT"),
        endereco=_parse_endereco(end_node) if end_node is not None else Endereco(),
    )


def _parse_destinatario(dest_elem) -> Destinatario:
    end_node = _primeiro_no(dest_elem, "nfe:enderDest")
    return Destinatario(
        cnpj=_texto(dest_elem, "nfe:CNPJ"),
        cpf=_texto(dest_elem, "nfe:CPF"),
        id_estrangeiro=_texto(dest_elem, "nfe:idEstrangeiro"),
        nome=_texto(dest_elem, "nfe:xNome"),
        ie=_texto(dest_elem, "nfe:IE"),
        email=_texto(dest_elem, "nfe:email"),
        endereco=_parse_endereco(end_node) if end_node is not None else Endereco(),
    )


def _parse_imposto_aliq(imposto_elem, xpath_aliq: str, xpath_qtde: str):
    """Retorna o primeiro nó de imposto por alíquota ou quantidade."""
    no = _primeiro_no(imposto_elem, xpath_aliq)
    return no if no is not None else _primeiro_no(imposto_elem, xpath_qtde)


def _parse_tributacao(imposto_elem) -> TributacaoItem:
    trib = TributacaoItem()

    # ICMS – aceita qualquer subgrupo (ICMS00, ICMS10, ICMSSN...)
    icms_grupos = imposto_elem.xpath("nfe:ICMS/*", namespaces=NS)
    if icms_grupos:
        g = icms_grupos[0]
        trib.icms_orig = _texto(g, "nfe:orig")
        trib.icms_cst = _texto(g, "nfe:CST") or _texto(g, "nfe:CSOSN")
        trib.icms_modbc = _texto(g, "nfe:modBC")
        trib.icms_vbc = _to_decimal(_texto(g, "nfe:vBC"))
        trib.icms_paliq = _to_decimal(_texto(g, "nfe:pICMS"))
        trib.icms_vicms = _to_decimal(_texto(g, "nfe:vICMS"))
        trib.icms_credpres = (
            _to_decimal(_texto(g, "nfe:pCredSN"))
            or _to_decimal(_texto(g, "nfe:vCredICMSSN"))
        )

    # IPI
    ipi_no = _primeiro_no(imposto_elem, "nfe:IPI/nfe:IPITrib")
    if ipi_no is not None:
        trib.ipi_cst = _texto(ipi_no, "nfe:CST")
        trib.ipi_vbc = _to_decimal(_texto(ipi_no, "nfe:vBC"))
        trib.ipi_paliq = _to_decimal(_texto(ipi_no, "nfe:pIPI"))
        trib.ipi_vipi = _to_decimal(_texto(ipi_no, "nfe:vIPI"))

    # PIS — captura valor de todos os grupos: PISAliq, PISQtde, PISOutr, PISNT
    pis_no = _parse_imposto_aliq(imposto_elem, "nfe:PIS/nfe:PISAliq", "nfe:PIS/nfe:PISQtde")
    if pis_no is None:
        pis_no = _primeiro_no(imposto_elem, "nfe:PIS/nfe:PISOutr")
    if pis_no is not None:
        trib.pis_cst = _texto(pis_no, "nfe:CST")
        trib.pis_vbc = _to_decimal(_texto(pis_no, "nfe:vBC"))
        trib.pis_paliq = _to_decimal(_texto(pis_no, "nfe:pPIS"))
        trib.pis_vpis = _to_decimal(_texto(pis_no, "nfe:vPIS"))
    else:
        # PISNT (CST 04-09): não tributado, vPIS = 0 mas CST deve ser registrado
        pisnt_no = _primeiro_no(imposto_elem, "nfe:PIS/nfe:PISNT")
        if pisnt_no is not None:
            trib.pis_cst = _texto(pisnt_no, "nfe:CST")

    # COFINS — captura valor de todos os grupos: COFINSAliq, COFINSQtde, COFINSOutr, COFINSNT
    cof_no = _parse_imposto_aliq(
        imposto_elem, "nfe:COFINS/nfe:COFINSAliq", "nfe:COFINS/nfe:COFINSQtde"
    )
    if cof_no is None:
        cof_no = _primeiro_no(imposto_elem, "nfe:COFINS/nfe:COFINSOutr")
    if cof_no is not None:
        trib.cofins_cst = _texto(cof_no, "nfe:CST")
        trib.cofins_vbc = _to_decimal(_texto(cof_no, "nfe:vBC"))
        trib.cofins_paliq = _to_decimal(_texto(cof_no, "nfe:pCOFINS"))
        trib.cofins_vcofins = _to_decimal(_texto(cof_no, "nfe:vCOFINS"))
    else:
        # COFINSNT (CST 04-09): não tributado, vCOFINS = 0 mas CST deve ser registrado
        cofinsnt_no = _primeiro_no(imposto_elem, "nfe:COFINS/nfe:COFINSNT")
        if cofinsnt_no is not None:
            trib.cofins_cst = _texto(cofinsnt_no, "nfe:CST")

    return trib


def _parse_produto(det_elem, num_item: int) -> Produto:
    prod_no = _primeiro_no(det_elem, "nfe:prod")
    if prod_no is None:
        return Produto(num_item=num_item)

    valor_bruto = _to_decimal(_texto(prod_no, "nfe:vProd"))
    valor_desconto = _to_decimal(_texto(prod_no, "nfe:vDesc"))

    produto = Produto(
        num_item=num_item,
        codigo=_texto(prod_no, "nfe:cProd"),
        ean=_texto(prod_no, "nfe:cEAN"),
        descricao=_texto(prod_no, "nfe:xProd"),
        ncm=_texto(prod_no, "nfe:NCM"),
        cfop=_texto(prod_no, "nfe:CFOP"),
        unidade=_texto(prod_no, "nfe:uCom"),
        quantidade=_to_decimal(_texto(prod_no, "nfe:qCom")),
        valor_unitario=_to_decimal(_texto(prod_no, "nfe:vUnCom")),
        valor_bruto=valor_bruto,
        valor_desconto=valor_desconto,
        valor_total=valor_bruto - valor_desconto,
    )

    imposto_no = _primeiro_no(det_elem, "nfe:imposto")
    if imposto_no is not None:
        produto.tributacao = _parse_tributacao(imposto_no)

    return produto


def _parse_totais(total_elem) -> Totais:
    icms_no = _primeiro_no(total_elem, "nfe:ICMSTot")
    if icms_no is None:
        return Totais()

    return Totais(
        v_bc=_to_decimal(_texto(icms_no, "nfe:vBC")),
        v_icms=_to_decimal(_texto(icms_no, "nfe:vICMS")),
        v_icms_deson=_to_decimal(_texto(icms_no, "nfe:vICMSDeson")),
        v_fcp=_to_decimal(_texto(icms_no, "nfe:vFCP")),
        v_bcsT=_to_decimal(_texto(icms_no, "nfe:vBCST")),
        v_st=_to_decimal(_texto(icms_no, "nfe:vST")),
        v_prod=_to_decimal(_texto(icms_no, "nfe:vProd")),
        v_frete=_to_decimal(_texto(icms_no, "nfe:vFrete")),
        v_seg=_to_decimal(_texto(icms_no, "nfe:vSeg")),
        v_desc=_to_decimal(_texto(icms_no, "nfe:vDesc")),
        v_ipi=_to_decimal(_texto(icms_no, "nfe:vIPI")),
        v_pis=_to_decimal(_texto(icms_no, "nfe:vPIS")),
        v_cofins=_to_decimal(_texto(icms_no, "nfe:vCOFINS")),
        v_outro=_to_decimal(_texto(icms_no, "nfe:vOutro")),
        v_nf=_to_decimal(_texto(icms_no, "nfe:vNF")),
    )


def _extrair_identificacao(inf, resultado: ResultadoLeitura) -> None:
    """Preenche os campos de identificação da NF-e no resultado."""
    chave_raw = inf.get("Id", "")
    resultado.chave_acesso = chave_raw.replace("NFe", "")

    ide_no = _primeiro_no(inf, "nfe:ide")
    if ide_no is not None:
        resultado.numero_nf = _texto(ide_no, "nfe:nNF")
        resultado.serie = _texto(ide_no, "nfe:serie")
        resultado.data_emissao = _texto(ide_no, "nfe:dhEmi")
        resultado.natureza_operacao = _texto(ide_no, "nfe:natOp")
        resultado.tipo_nf = _texto(ide_no, "nfe:tpNF")


# ---------------------------------------------------------------------------
# Agente 1 – classe principal
# ---------------------------------------------------------------------------

class AgenteLeitorNFe:
    """
    Lê e extrai dados de NF-e XML v4.00.
    Suporta nfeProc (NF-e processada) e NFe direta.
    """

    def __init__(self, validar_schema: bool = False):
        self._schema: Optional[etree.XMLSchema] = _carregar_schema() if validar_schema else None

    def ler_arquivo(self, caminho: str) -> ResultadoLeitura:
        """Lê NF-e a partir de um caminho de arquivo."""
        resultado = ResultadoLeitura()
        if not os.path.exists(caminho):
            resultado.erros.append(f"Arquivo não encontrado: {caminho}")
            return resultado
        try:
            with open(caminho, "rb") as f:
                return self.ler_bytes(f.read())
        except OSError as exc:
            resultado.erros.append(f"Erro ao ler arquivo: {exc}")
            return resultado

    def ler_bytes(self, conteudo: bytes) -> ResultadoLeitura:
        """Lê NF-e a partir de bytes XML."""
        resultado = ResultadoLeitura()

        # Parser seguro: desabilita entidades externas (XXE) e acesso à rede
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        try:
            raiz = etree.fromstring(conteudo, parser)
        except etree.XMLSyntaxError as exc:
            resultado.erros.append(f"XML inválido: {exc}")
            return resultado

        if self._schema and not self._schema.validate(raiz):
            for err in self._schema.error_log:
                resultado.erros.append(f"XSD: {err.message}")

        inf_nos = raiz.xpath("//nfe:infNFe", namespaces=NS)
        if not inf_nos:
            resultado.erros.append("Elemento infNFe não encontrado no XML.")
            return resultado

        return _popular_resultado(inf_nos[0])


def _carregar_schema() -> Optional[etree.XMLSchema]:
    """Carrega o schema XSD; retorna None se não disponível."""
    if not os.path.exists(XSD_PATH):
        return None
    try:
        return etree.XMLSchema(etree.parse(XSD_PATH))
    except Exception:
        return None


def _popular_resultado(inf) -> ResultadoLeitura:
    """Preenche um ResultadoLeitura a partir do nó infNFe."""
    resultado = ResultadoLeitura()

    _extrair_identificacao(inf, resultado)

    emit_no = _primeiro_no(inf, "nfe:emit")
    if emit_no is not None:
        resultado.emitente = _parse_emitente(emit_no)

    dest_no = _primeiro_no(inf, "nfe:dest")
    if dest_no is not None:
        resultado.destinatario = _parse_destinatario(dest_no)

    for det in inf.xpath("nfe:det", namespaces=NS):
        num = int(det.get("nItem", 0))
        resultado.produtos.append(_parse_produto(det, num))

    total_no = _primeiro_no(inf, "nfe:total")
    if total_no is not None:
        resultado.totais = _parse_totais(total_no)

    return resultado
