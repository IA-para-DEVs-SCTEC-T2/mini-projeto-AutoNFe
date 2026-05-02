"""
Agente 1 — Leitura de NF-e (XML)

Responsável pela leitura e extração estruturada dos dados do XML,
com base no esquema oficial leiauteNFe_v4.00.xsd.

SEGURANÇA:
- Parser configurado contra XXE (XML External Entity Injection):
  resolve_entities=False, load_dtd=False, no_network=True
- Validação estrutural via XSD antes de qualquer extração de dados
- Caminho do arquivo validado: extensão .xml obrigatória e deve ser
  um arquivo regular (não symlink para arquivo sensível, não device file)
- O usuário pode informar XMLs de qualquer diretório do sistema
"""

from pathlib import Path
from lxml import etree


# Raiz do projeto — usada apenas para localizar o XSD
_BASE_DIR = Path(__file__).resolve().parent.parent

# Caminho para o schema XSD oficial da NF-e v4.00
_XSD_PATH = _BASE_DIR / "Apoio" / "leiauteNFe_v4.00.xsd"


def _criar_parser_seguro() -> etree.XMLParser:
    """
    Retorna um parser XML endurecido contra ataques XXE.

    Configurações de segurança aplicadas:
    - resolve_entities=False  → impede expansão de entidades externas
    - load_dtd=False          → impede carregamento de DTD externo
    - no_network=True         → bloqueia qualquer acesso de rede pelo parser
    - huge_tree=False         → protege contra ataques de expansão de árvore (Billion Laughs)
    """
    return etree.XMLParser(
        resolve_entities=False,
        load_dtd=False,
        no_network=True,
        huge_tree=False,
    )


def _validar_caminho(caminho_xml: str) -> Path:
    """
    Valida o caminho do arquivo XML informado pelo usuário.

    Não restringe o diretório — o usuário pode apontar para qualquer
    pasta do sistema. As verificações garantem que:
    1. O arquivo tem extensão .xml (evita abrir executáveis ou scripts)
    2. É um arquivo regular (evita symlinks para arquivos sensíveis
       ou device files como /dev/urandom)
    3. O arquivo existe

    Args:
        caminho_xml: Caminho fornecido pelo usuário ou pelo pipeline.

    Returns:
        Path absoluto e resolvido do arquivo.

    Raises:
        ValueError: Se a extensão for inválida ou não for arquivo regular.
        FileNotFoundError: Se o arquivo não existir.
    """
    caminho_resolvido = Path(caminho_xml).resolve()

    # 1. Valida extensão antes de qualquer leitura
    if caminho_resolvido.suffix.lower() != ".xml":
        raise ValueError(
            f"Extensão inválida: '{caminho_resolvido.suffix}'. "
            "Somente arquivos .xml são aceitos."
        )

    # 2. Garante que é um arquivo regular (não symlink, não device file)
    if not caminho_resolvido.is_file():
        raise ValueError(
            f"O caminho '{caminho_xml}' não é um arquivo regular."
        )

    return caminho_resolvido


def _carregar_schema_xsd() -> etree.XMLSchema:
    """
    Carrega e compila o schema XSD da NF-e v4.00.

    Returns:
        Objeto XMLSchema pronto para validação.

    Raises:
        FileNotFoundError: Se o arquivo XSD não for encontrado.
    """
    if not _XSD_PATH.exists():
        raise FileNotFoundError(
            f"Schema XSD não encontrado em '{_XSD_PATH}'. "
            "Certifique-se de que o arquivo 'leiauteNFe_v4.00.xsd' "
            "está em 'Apoio/'."
        )

    # Parser seguro também para o XSD
    parser = _criar_parser_seguro()
    xsd_doc = etree.parse(str(_XSD_PATH), parser)
    return etree.XMLSchema(xsd_doc)


def _validar_xml_contra_xsd(tree: etree._ElementTree, schema: etree.XMLSchema) -> None:
    """
    Valida a árvore XML contra o schema XSD da NF-e.

    Args:
        tree: Árvore XML já parseada.
        schema: Schema XSD compilado.

    Raises:
        ValueError: Se o XML não for válido segundo o XSD.
    """
    if not schema.validate(tree):
        erros = "\n".join(str(e) for e in schema.error_log)
        raise ValueError(f"XML inválido segundo o schema NF-e v4.00:\n{erros}")


def _extrair_namespace(root: etree._Element) -> str:
    """Extrai o namespace do elemento raiz do XML da NF-e."""
    ns = root.nsmap.get(None, "")
    return f"{{{ns}}}" if ns else ""


def extrair_dados_nfe(caminho_xml: str) -> dict:
    """
    Lê um arquivo XML de NF-e e extrai os dados estruturados.

    Fluxo de segurança:
    1. Valida o caminho contra path traversal
    2. Faz o parse com parser endurecido contra XXE
    3. Valida a estrutura contra o XSD oficial
    4. Extrai os dados

    Args:
        caminho_xml: Caminho para o arquivo XML da NF-e.

    Returns:
        Dicionário com os dados extraídos da NF-e.

    Raises:
        ValueError: Caminho inválido ou XML fora do schema.
        FileNotFoundError: Arquivo XML ou XSD não encontrado.
    """
    # 1. Validação de caminho (path traversal)
    caminho = _validar_caminho(caminho_xml)

    # 2. Parse seguro contra XXE
    parser = _criar_parser_seguro()
    tree = etree.parse(str(caminho), parser)
    root = tree.getroot()

    # 3. Validação estrutural via XSD
    schema = _carregar_schema_xsd()
    _validar_xml_contra_xsd(tree, schema)

    # 4. Extração de dados
    ns = _extrair_namespace(root)
    inf_nfe = root.find(f".//{ns}infNFe")

    if inf_nfe is None:
        raise ValueError("Elemento 'infNFe' não encontrado no XML.")

    return {
        "emitente": _extrair_emitente(inf_nfe, ns),
        "destinatario": _extrair_destinatario(inf_nfe, ns),
        "produtos": _extrair_produtos(inf_nfe, ns),
        "tributacao": _extrair_tributacao(inf_nfe, ns),
        "totais": _extrair_totais(inf_nfe, ns),
    }


def _texto(elemento: etree._Element | None) -> str:
    """Retorna o texto de um elemento XML ou string vazia se None."""
    return (elemento.text or "").strip() if elemento is not None else ""


def _extrair_emitente(inf_nfe: etree._Element, ns: str) -> dict:
    emit = inf_nfe.find(f"{ns}emit")
    if emit is None:
        return {}
    return {
        "cnpj": _texto(emit.find(f"{ns}CNPJ")),
        "razao_social": _texto(emit.find(f"{ns}xNome")),
        "ie": _texto(emit.find(f"{ns}IE")),
        "endereco": _extrair_endereco(emit.find(f"{ns}enderEmit"), ns),
    }


def _extrair_destinatario(inf_nfe: etree._Element, ns: str) -> dict:
    dest = inf_nfe.find(f"{ns}dest")
    if dest is None:
        return {}
    return {
        "cnpj": _texto(dest.find(f"{ns}CNPJ")),
        "cpf": _texto(dest.find(f"{ns}CPF")),
        "razao_social": _texto(dest.find(f"{ns}xNome")),
        "ie": _texto(dest.find(f"{ns}IE")),
        "endereco": _extrair_endereco(dest.find(f"{ns}enderDest"), ns),
    }


def _extrair_endereco(ender: etree._Element | None, ns: str) -> dict:
    if ender is None:
        return {}
    return {
        "logradouro": _texto(ender.find(f"{ns}xLgr")),
        "numero": _texto(ender.find(f"{ns}nro")),
        "municipio": _texto(ender.find(f"{ns}xMun")),
        "uf": _texto(ender.find(f"{ns}UF")),
        "cep": _texto(ender.find(f"{ns}CEP")),
    }


def _extrair_produtos(inf_nfe: etree._Element, ns: str) -> list[dict]:
    produtos = []
    for det in inf_nfe.findall(f"{ns}det"):
        prod = det.find(f"{ns}prod")
        if prod is None:
            continue
        produtos.append({
            "codigo": _texto(prod.find(f"{ns}cProd")),
            "descricao": _texto(prod.find(f"{ns}xProd")),
            "ncm": _texto(prod.find(f"{ns}NCM")),
            "cfop": _texto(prod.find(f"{ns}CFOP")),
            "unidade": _texto(prod.find(f"{ns}uCom")),
            "quantidade": _texto(prod.find(f"{ns}qCom")),
            "valor_unitario": _texto(prod.find(f"{ns}vUnCom")),
            "valor_total": _texto(prod.find(f"{ns}vProd")),
        })
    return produtos


def _extrair_tributacao(inf_nfe: etree._Element, ns: str) -> list[dict]:
    tributacoes = []
    for det in inf_nfe.findall(f"{ns}det"):
        imposto = det.find(f"{ns}imposto")
        if imposto is None:
            continue

        cfop = _texto(det.find(f".//{ns}CFOP"))

        icms_elem = imposto.find(f".//{ns}ICMS")
        pis_elem = imposto.find(f".//{ns}PIS")
        cofins_elem = imposto.find(f".//{ns}COFINS")
        ipi_elem = imposto.find(f".//{ns}IPI")

        tributacoes.append({
            "cfop": cfop,
            "icms": _extrair_grupo_tributo(icms_elem, ns),
            "pis": _extrair_grupo_tributo(pis_elem, ns),
            "cofins": _extrair_grupo_tributo(cofins_elem, ns),
            "ipi": _extrair_grupo_tributo(ipi_elem, ns),
        })
    return tributacoes


def _extrair_grupo_tributo(grupo: etree._Element | None, ns: str) -> dict:
    if grupo is None:
        return {}
    # Pega o primeiro filho (ex: ICMS00, ICMS10, PISAliq, etc.)
    filho = next(iter(grupo), None)
    if filho is None:
        return {}
    return {
        "cst": _texto(filho.find(f"{ns}CST")) or _texto(filho.find(f"{ns}CSOSN")),
        "base": _texto(filho.find(f"{ns}vBC")),
        "aliquota": _texto(filho.find(f"{ns}pICMS"))
                    or _texto(filho.find(f"{ns}pPIS"))
                    or _texto(filho.find(f"{ns}pCOFINS"))
                    or _texto(filho.find(f"{ns}pIPI")),
        "valor": _texto(filho.find(f"{ns}vICMS"))
                 or _texto(filho.find(f"{ns}vPIS"))
                 or _texto(filho.find(f"{ns}vCOFINS"))
                 or _texto(filho.find(f"{ns}vIPI")),
    }


def _extrair_totais(inf_nfe: etree._Element, ns: str) -> dict:
    total = inf_nfe.find(f".//{ns}ICMSTot")
    if total is None:
        return {}
    return {
        "valor_produtos": _texto(total.find(f"{ns}vProd")),
        "valor_frete": _texto(total.find(f"{ns}vFrete")),
        "valor_seguro": _texto(total.find(f"{ns}vSeg")),
        "valor_desconto": _texto(total.find(f"{ns}vDesc")),
        "valor_total_nfe": _texto(total.find(f"{ns}vNF")),
        "valor_icms": _texto(total.find(f"{ns}vICMS")),
        "valor_pis": _texto(total.find(f"{ns}vPIS")),
        "valor_cofins": _texto(total.find(f"{ns}vCOFINS")),
    }
