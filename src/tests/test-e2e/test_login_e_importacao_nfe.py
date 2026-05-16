"""
Testes E2E — AutoNFe
Cenários cobertos:
  1. Login com credenciais válidas
  2. Importação de NF-e via upload de XML após login

Pré-requisitos:
  - Aplicação rodando em http://127.0.0.1:5000
  - Usuário test-autonfe com senha AutoNfe123# cadastrado
  - Arquivo src/data/xml_samples/NFe4.xml presente no projeto

Execução:
  pytest src/tests/test-e2e/test_login_e_importacao_nfe.py -v
"""

import os
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

BASE_URL = "http://127.0.0.1:5000"
EMAIL = "test-autonfe"       # login pelo nome de usuário
SENHA = "AutoNfe123#"

# Caminho absoluto para o XML de exemplo usado na importação
XML_NFE4 = str(
    Path(__file__).parent.parent.parent / "data" / "xml_samples" / "NFe4.xml"
)


# ---------------------------------------------------------------------------
# Fixture: abre o browser com slow_mo para melhor observabilidade
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def pagina(page: Page) -> Page:
    """Retorna a página Playwright configurada com timeout padrão de 10s."""
    page.set_default_timeout(10_000)
    return page


# ---------------------------------------------------------------------------
# Teste 1 — Login com credenciais válidas
# ---------------------------------------------------------------------------

def test_login_com_credenciais_validas(pagina: Page) -> None:
    """
    Verifica que o usuário consegue fazer login com e-mail e senha válidos
    e é redirecionado para o dashboard principal (URL raiz '/').
    """
    # Acessa a tela de login
    pagina.goto(f"{BASE_URL}/login")

    # Confirma que a página de login foi carregada pelo título
    expect(pagina).to_have_title("AutoNFe — Login")

    # Preenche o campo de usuário/e-mail
    pagina.fill("input[name='login']", EMAIL)

    # Preenche o campo de senha
    pagina.fill("input[name='senha']", SENHA)

    # Clica no botão "Entrar"
    pagina.click("button[type='submit']")

    # Aguarda o redirecionamento para o dashboard (URL raiz)
    pagina.wait_for_url(f"{BASE_URL}/", timeout=10_000)

    # Valida que a URL atual é o dashboard
    expect(pagina).to_have_url(f"{BASE_URL}/")

    # Valida que o título da página do dashboard está correto
    expect(pagina).to_have_title("AutoNFe — SCTEC")

    # Valida que o menu lateral está visível (confirma que o login foi bem-sucedido)
    expect(pagina.locator(".sidebar")).to_be_visible()

    # Valida que o botão de navegação "Importar NF-e" está presente na sidebar
    expect(pagina.locator("button[data-view='importar']")).to_be_visible()


# ---------------------------------------------------------------------------
# Teste 2 — Importação de NF-e após login
# ---------------------------------------------------------------------------

def test_importacao_nfe_apos_login(pagina: Page) -> None:
    """
    Verifica o fluxo completo de importação de NF-e:
      1. Faz login com credenciais válidas
      2. Navega para a seção "Importar NF-e"
      3. Faz upload do arquivo NFe4.xml
      4. Valida que a importação foi processada com sucesso
    """
    # Garante que o arquivo XML existe antes de executar o teste
    assert os.path.exists(XML_NFE4), (
        f"Arquivo XML não encontrado: {XML_NFE4}\n"
        "Verifique se src/data/xml_samples/NFe4.xml existe no projeto."
    )

    # ── Etapa 1: Login ──────────────────────────────────────────────────────
    pagina.goto(f"{BASE_URL}/login")

    pagina.fill("input[name='login']", EMAIL)
    pagina.fill("input[name='senha']", SENHA)
    pagina.click("button[type='submit']")

    # Aguarda redirecionamento para o dashboard
    pagina.wait_for_url(f"{BASE_URL}/", timeout=10_000)

    # Confirma que o login foi bem-sucedido
    expect(pagina).to_have_url(f"{BASE_URL}/")

    # ── Etapa 2: Navegar para "Importar NF-e" ───────────────────────────────
    # Clica no item de menu "Importar NF-e" na sidebar
    pagina.click("button[data-view='importar']")

    # Aguarda a seção de importação ficar visível
    secao_importar = pagina.locator("#view-importar")
    expect(secao_importar).to_be_visible()

    # Valida que o título da seção está correto
    expect(secao_importar.locator("h1.page-title")).to_have_text("Importar NF-e")

    # Valida que a área de upload está visível
    expect(pagina.locator("#uploadArea")).to_be_visible()

    # ── Etapa 3: Upload do arquivo XML ──────────────────────────────────────
    # Define o arquivo no input de upload (sem abrir o diálogo do sistema)
    pagina.locator("#fileInput").set_input_files(XML_NFE4)

    # ── Etapa 4: Aguarda e valida o resultado da importação ─────────────────
    # O JS exibe "Processando..." e depois substitui pelo resultado final.
    # Aguarda até que o texto de processamento desapareça e o resultado final apareça.
    resultado = pagina.locator("#importResult")
    expect(resultado).to_be_visible(timeout=15_000)

    # Aguarda o texto "Processando" sumir — indica que a resposta da API chegou
    expect(resultado).not_to_contain_text("Processando", timeout=20_000)

    # Valida que o resultado não está oculto (classe 'hidden' removida pelo JS)
    expect(resultado).not_to_have_class("hidden")

    # Valida que o resultado contém indicação de sucesso
    # O sistema exibe "sucesso" ou o número da NF-e no resultado
    resultado_texto = resultado.inner_text()
    assert (
        "sucesso" in resultado_texto.lower()
        or "nf-e" in resultado_texto.lower()
        or "importad" in resultado_texto.lower()
    ), (
        f"Resultado da importação não indica sucesso.\n"
        f"Texto encontrado: {resultado_texto}"
    )
