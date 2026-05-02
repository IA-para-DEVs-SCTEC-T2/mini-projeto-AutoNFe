"""
AutoNFe — Ponto de entrada do pipeline multi-agente.

Uso:
    python main.py --arquivo caminho/para/nota.xml
    python main.py  (processa todos os XMLs em data/xmls/)
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()  # carrega variáveis do .env antes de qualquer import do projeto

from database.conexao import inicializar_banco
from agents.agente1_leitura import extrair_dados_nfe
from agents.agente2_cadastro import processar as agente2_processar


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AutoNFe — Processamento de NF-e via agentes de IA"
    )
    parser.add_argument(
        "--arquivo",
        type=str,
        help="Caminho para o arquivo XML da NF-e a ser processado.",
    )
    return parser.parse_args()


def processar_arquivo(caminho_xml: str) -> None:
    """
    Executa o pipeline completo para um único arquivo XML.

    Args:
        caminho_xml: Caminho para o arquivo XML da NF-e.
    """
    print(f"\n[Agente 1] Lendo: {caminho_xml}")
    dados = extrair_dados_nfe(caminho_xml)
    print(f"  Emitente : {dados['emitente'].get('razao_social', '-')}")
    print(f"  Destinat.: {dados['destinatario'].get('razao_social', '-')}")
    print(f"  Produtos : {len(dados['produtos'])} item(ns)")

    print("\n[Agente 2] Cadastrando entidades...")
    resultado = agente2_processar(dados)
    print(f"  Emitente    : {resultado['emitente']['acao']} (id={resultado['emitente']['id']})")
    print(f"  Destinatário: {resultado['destinatario']['acao']} (id={resultado['destinatario']['id']})")
    print(f"  Tributações : {len(resultado['tributacao'])} processada(s)")


def main() -> None:
    inicializar_banco()
    args = _parse_args()

    if args.arquivo:
        try:
            processar_arquivo(args.arquivo)
        except (ValueError, FileNotFoundError) as exc:
            print(f"[ERRO] {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        # Processa todos os XMLs em data/xmls/ se nenhum arquivo for informado
        pasta_xmls = Path(__file__).resolve().parent / "data" / "xmls"
        if not pasta_xmls.exists():
            print(
                "Nenhum arquivo informado e pasta 'data/xmls/' não encontrada.\n"
                "Use: python main.py --arquivo caminho/para/nota.xml",
                file=sys.stderr,
            )
            sys.exit(1)

        xmls = list(pasta_xmls.glob("*.xml"))
        if not xmls:
            print("Nenhum arquivo XML encontrado em 'data/xmls/'.", file=sys.stderr)
            sys.exit(1)

        for xml in xmls:
            try:
                processar_arquivo(str(xml))
            except (ValueError, FileNotFoundError) as exc:
                print(f"[ERRO] {xml.name}: {exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
