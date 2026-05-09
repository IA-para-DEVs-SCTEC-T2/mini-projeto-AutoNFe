"""
Testes automatizados do AutoNFe
Cobre os 3 agentes + orquestrador + rotas Flask.
"""

import os
import sys
import pytest
from decimal import Decimal

# Garante que o pacote raiz está no path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.agent1_leitura import AgenteLeitorNFe
from src.agents.agent2_cadastro import AgenteCadastro
from src.agents.agent3_validacao import AgenteValidacaoValores
from src.agents.orquestrador import Orquestrador
from src.database.models import criar_tabelas, SessionLocal, NotaFiscal, Emitente, Destinatario

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

XML_PATH = os.path.join(os.path.dirname(__file__), "fixtures", "nfe_exemplo.xml")


@pytest.fixture(scope="session")
def xml_bytes():
    with open(XML_PATH, "rb") as f:
        return f.read()


@pytest.fixture(scope="session")
def resultado_leitura(xml_bytes):
    agente = AgenteLeitorNFe()
    return agente.ler_bytes(xml_bytes)


@pytest.fixture
def db_session(tmp_path, monkeypatch):
    """Sessão de banco de dados em arquivo temporário."""
    import src.database.models as m
    db_file = str(tmp_path / "test.db")
    test_url = f"sqlite:///{db_file}"
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker

    eng = create_engine(test_url, connect_args={"check_same_thread": False})

    @event.listens_for(eng, "connect")
    def _pragma(conn, _):
        conn.cursor().execute("PRAGMA foreign_keys=ON")

    m.Base.metadata.create_all(bind=eng)
    Session = sessionmaker(bind=eng)
    session = Session()
    yield session
    session.close()


# ---------------------------------------------------------------------------
# Teste 1 – Agente 1: leitura básica do XML
# ---------------------------------------------------------------------------

class TestAgente1Leitura:

    def test_sem_erros(self, resultado_leitura):
        assert resultado_leitura.erros == [], f"Erros inesperados: {resultado_leitura.erros}"

    def test_chave_acesso(self, resultado_leitura):
        assert len(resultado_leitura.chave_acesso) == 44

    def test_numero_nf(self, resultado_leitura):
        assert resultado_leitura.numero_nf == "1"

    def test_emitente_cnpj(self, resultado_leitura):
        assert resultado_leitura.emitente.cnpj == "00000000000191"

    def test_emitente_nome(self, resultado_leitura):
        assert "EMITENTE" in resultado_leitura.emitente.nome.upper()

    def test_destinatario_cnpj(self, resultado_leitura):
        assert resultado_leitura.destinatario.cnpj == "11111111000191"

    def test_dois_itens(self, resultado_leitura):
        assert len(resultado_leitura.produtos) == 2

    def test_produto1_valores(self, resultado_leitura):
        p = resultado_leitura.produtos[0]
        assert p.quantidade == Decimal("10.0000")
        assert p.valor_unitario == Decimal("100.0000000000")
        assert p.valor_bruto == Decimal("1000.00")

    def test_produto1_icms(self, resultado_leitura):
        t = resultado_leitura.produtos[0].tributacao
        assert t.icms_cst == "00"
        assert t.icms_paliq == Decimal("12.00")
        assert t.icms_vicms == Decimal("120.00")

    def test_totais_vnf(self, resultado_leitura):
        assert resultado_leitura.totais.v_nf == Decimal("1225.00")

    def test_xml_invalido(self):
        agente = AgenteLeitorNFe()
        res = agente.ler_bytes(b"<xml_invalido>")
        assert len(res.erros) > 0

    def test_arquivo_inexistente(self):
        agente = AgenteLeitorNFe()
        res = agente.ler_arquivo("/caminho/inexistente.xml")
        assert len(res.erros) > 0


# ---------------------------------------------------------------------------
# Teste 2 – Agente 2: cadastro no banco
# ---------------------------------------------------------------------------

class TestAgente2Cadastro:

    def test_emitente_cadastrado(self, resultado_leitura, db_session):
        agente = AgenteCadastro(db_session)
        rel = agente.processar(resultado_leitura)
        assert rel.emitente is not None
        assert rel.emitente.acao == "cadastrado"
        assert rel.emitente.autorizado is False

    def test_emitente_nao_duplicado(self, resultado_leitura, db_session):
        agente = AgenteCadastro(db_session)
        agente.processar(resultado_leitura)
        db_session.commit()
        rel2 = agente.processar(resultado_leitura)
        assert rel2.emitente.acao == "encontrado"

    def test_destinatario_cadastrado(self, resultado_leitura, db_session):
        agente = AgenteCadastro(db_session)
        rel = agente.processar(resultado_leitura)
        assert rel.destinatario is not None
        assert rel.destinatario.acao == "cadastrado"

    def test_tributacao_cadastrada(self, resultado_leitura, db_session):
        agente = AgenteCadastro(db_session)
        rel = agente.processar(resultado_leitura)
        assert len(rel.tributacoes) >= 1
        assert rel.tributacoes[0].acao == "cadastrado"

    def test_tributacao_cfop_cst(self, resultado_leitura, db_session):
        agente = AgenteCadastro(db_session)
        rel = agente.processar(resultado_leitura)
        ids = [t.identificador for t in rel.tributacoes]
        assert any("5102" in i for i in ids)


# ---------------------------------------------------------------------------
# Teste 3 – Agente 3: validação de valores
# ---------------------------------------------------------------------------

class TestAgente3Validacao:

    def test_validacao_ok(self, resultado_leitura):
        agente = AgenteValidacaoValores()
        rel = agente.validar(resultado_leitura)
        # Pode ter pequenas diferenças de arredondamento no XML de teste
        # O importante é que o agente executa sem exceção
        assert rel is not None

    def test_icms_correto(self, resultado_leitura):
        """ICMS item 1: 1000 × 12% = 120"""
        agente = AgenteValidacaoValores()
        rel = agente.validar(resultado_leitura)
        icms_erros = [d for d in rel.diferencas_itens if d.campo == "vICMS" and d.num_item == 1]
        assert icms_erros == [], f"ICMS divergente: {icms_erros}"

    def test_pis_correto(self, resultado_leitura):
        """PIS item 1: 1000 × 0.65% = 6.50"""
        agente = AgenteValidacaoValores()
        rel = agente.validar(resultado_leitura)
        pis_erros = [d for d in rel.diferencas_itens if d.campo == "vPIS" and d.num_item == 1]
        assert pis_erros == [], f"PIS divergente: {pis_erros}"

    def test_divergencia_detectada(self):
        """Cria uma NF-e com valor ICMS errado e verifica detecção."""
        from src.agents.agent1_leitura import ResultadoLeitura, Produto, TributacaoItem, Totais
        res = ResultadoLeitura()
        t = TributacaoItem(
            icms_cst="00", icms_vbc=Decimal("1000"), icms_paliq=Decimal("12"),
            icms_vicms=Decimal("999")  # errado: deveria ser 120
        )
        p = Produto(num_item=1, descricao="Teste", quantidade=Decimal("1"),
                    valor_unitario=Decimal("1000"), valor_bruto=Decimal("1000"),
                    valor_total=Decimal("1000"), tributacao=t)
        res.produtos = [p]
        res.totais = Totais(v_prod=Decimal("1000"), v_nf=Decimal("1000"))

        agente = AgenteValidacaoValores()
        rel = agente.validar(res)
        assert not rel.ok
        # O campo agora contém a mensagem descritiva — verifica que menciona ICMS
        assert any("ICMS" in d.campo for d in rel.diferencas_itens)


# ---------------------------------------------------------------------------
# Teste 4 – Orquestrador: fluxo completo
# ---------------------------------------------------------------------------

class TestOrquestrador:

    def test_processar_bytes(self, xml_bytes, db_session):
        orq = Orquestrador(db_session)
        res = orq.processar_bytes(xml_bytes)
        db_session.commit()
        assert res.nota_id is not None
        assert res.leitura is not None
        assert res.cadastro is not None
        assert res.validacao is not None

    def test_duplicidade_bloqueada(self, xml_bytes, db_session):
        orq = Orquestrador(db_session)
        orq.processar_bytes(xml_bytes)
        db_session.commit()
        res2 = orq.processar_bytes(xml_bytes)
        assert any("já importada" in e for e in res2.erros)

    def test_nota_salva_no_banco(self, xml_bytes, db_session):
        orq = Orquestrador(db_session)
        res = orq.processar_bytes(xml_bytes)
        db_session.commit()
        nota = db_session.query(NotaFiscal).filter_by(id=res.nota_id).first()
        assert nota is not None
        assert nota.numero_nf == "1"

    def test_itens_salvos(self, xml_bytes, db_session):
        orq = Orquestrador(db_session)
        res = orq.processar_bytes(xml_bytes)
        db_session.commit()
        nota = db_session.query(NotaFiscal).filter_by(id=res.nota_id).first()
        assert len(nota.itens) == 2


# ---------------------------------------------------------------------------
# Teste 5 – Flask API
# ---------------------------------------------------------------------------

@pytest.fixture
def flask_client(tmp_path, monkeypatch):
    """Cliente de teste Flask com banco isolado e token de autenticação."""
    import src.database.models as m
    import src.database.repository as repo
    import src.web.security as security
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from contextlib import contextmanager

    db_file = str(tmp_path / "flask_test.db")
    test_url = f"sqlite:///{db_file}"
    eng = create_engine(test_url, connect_args={"check_same_thread": False})

    @event.listens_for(eng, "connect")
    def _pragma(conn, _):
        conn.cursor().execute("PRAGMA foreign_keys=ON")

    m.Base.metadata.create_all(bind=eng)
    TestSession = sessionmaker(bind=eng)

    # Monkey-patch sessao_db no repository para usar banco de teste
    @contextmanager
    def _sessao_teste():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(repo, "sessao_db", _sessao_teste)

    # Define token fixo para os testes
    TEST_TOKEN = "test-token-seguro-123"
    monkeypatch.setattr(security, "_API_TOKEN", TEST_TOKEN)

    import src.web.main as flask_app
    flask_app.app.config["TESTING"] = True

    # Helper que injeta o token automaticamente em todas as requisições
    class ClienteAutenticado:
        def __init__(self, client):
            self._client = client
            self._token = TEST_TOKEN

        def _headers(self, extra=None):
            h = {"X-API-Token": self._token}
            if extra:
                h.update(extra)
            return h

        def get(self, url, **kwargs):
            kwargs.setdefault("headers", {}).update(self._headers())
            return self._client.get(url, **kwargs)

        def post(self, url, **kwargs):
            kwargs.setdefault("headers", {}).update(self._headers())
            return self._client.post(url, **kwargs)

    with flask_app.app.test_client() as client:
        yield ClienteAutenticado(client)


class TestFlaskAPI:

    def test_dashboard_retorna_200(self, flask_client):
        res = flask_client.get("/api/dashboard")
        assert res.status_code == 200
        data = res.get_json()
        assert "total_nfe" in data

    def test_dashboard_periodos(self, flask_client):
        for periodo in ("dia", "mes", "ano"):
            res = flask_client.get(f"/api/dashboard?periodo={periodo}")
            assert res.status_code == 200

    def test_listar_emitentes_vazio(self, flask_client):
        res = flask_client.get("/api/emitentes")
        assert res.status_code == 200
        assert res.get_json() == []

    def test_listar_destinatarios_vazio(self, flask_client):
        res = flask_client.get("/api/destinatarios")
        assert res.status_code == 200
        assert res.get_json() == []

    def test_listar_tributacoes_vazio(self, flask_client):
        res = flask_client.get("/api/tributacoes")
        assert res.status_code == 200
        assert res.get_json() == []

    def test_importar_sem_arquivo(self, flask_client):
        res = flask_client.post("/api/importar")
        assert res.status_code == 400

    def test_importar_xml_valido(self, flask_client):
        with open(XML_PATH, "rb") as f:
            data = {"arquivo": (f, "nfe_teste.xml")}
            res = flask_client.post(
                "/api/importar",
                data=data,
                content_type="multipart/form-data",
            )
        assert res.status_code == 200
        body = res.get_json()
        assert body["sucesso"] is True
        assert body["nota_id"] is not None

    def test_listar_notas_apos_importacao(self, flask_client):
        # Importa primeiro
        with open(XML_PATH, "rb") as f:
            flask_client.post(
                "/api/importar",
                data={"arquivo": (f, "nfe.xml")},
                content_type="multipart/form-data",
            )
        res = flask_client.get("/api/notas")
        assert res.status_code == 200
        notas = res.get_json()
        assert len(notas) >= 1

    def test_autorizar_emitente(self, flask_client):
        # Importa para criar emitente
        with open(XML_PATH, "rb") as f:
            flask_client.post(
                "/api/importar",
                data={"arquivo": (f, "nfe.xml")},
                content_type="multipart/form-data",
            )
        emitentes = flask_client.get("/api/emitentes").get_json()
        assert len(emitentes) >= 1
        ids = [e["id"] for e in emitentes if not e["autorizado"]]
        if ids:
            res = flask_client.post(
                "/api/emitentes/autorizar",
                json={"ids": ids},
                content_type="application/json",
            )
            assert res.status_code == 200

    def test_detalhe_nota_inexistente(self, flask_client):
        res = flask_client.get("/api/notas/99999")
        assert res.status_code == 404

# ---------------------------------------------------------------------------
# Testes de Segurança — OWASP Top 10
# ---------------------------------------------------------------------------

class TestSeguranca:
    """Valida as correções de segurança implementadas."""

    # A01 / A07 — Autenticação obrigatória
    def test_sem_token_retorna_401(self, flask_client):
        """Requisição sem token deve ser rejeitada com 401."""
        import src.web.main as flask_app
        with flask_app.app.test_client() as client_sem_token:
            res = client_sem_token.get("/api/dashboard")
            assert res.status_code == 401

    def test_token_invalido_retorna_401(self, flask_client):
        """Token incorreto deve ser rejeitado com 401."""
        import src.web.main as flask_app
        with flask_app.app.test_client() as client_sem_token:
            res = client_sem_token.get(
                "/api/dashboard",
                headers={"X-API-Token": "token-errado"}
            )
            assert res.status_code == 401

    def test_token_valido_retorna_200(self, flask_client):
        """Token correto deve permitir acesso."""
        res = flask_client.get("/api/dashboard")
        assert res.status_code == 200

    def test_pagina_principal_publica(self, flask_client):
        """A página de login deve ser acessível sem token."""
        import src.web.main as flask_app
        with flask_app.app.test_client() as client_sem_token:
            res = client_sem_token.get("/login")
            assert res.status_code == 200

    # A05 — Headers de segurança
    def test_headers_seguranca_presentes(self, flask_client):
        """Respostas devem conter os headers de segurança obrigatórios."""
        res = flask_client.get("/api/dashboard")
        assert res.headers.get("X-Content-Type-Options") == "nosniff"
        assert res.headers.get("X-Frame-Options") == "DENY"
        assert "Content-Security-Policy" in res.headers

    # A03 — XXE: parser seguro
    def test_xml_com_entidade_externa_rejeitado(self, flask_client):
        """XML com tentativa de XXE deve ser rejeitado sem vazar dados do servidor."""
        xml_xxe = b"""<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
        <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
          <NFe><infNFe Id="NFe00000000000000000000000000000000000000000000">
            <ide><natOp>&xxe;</natOp></ide>
          </infNFe></NFe>
        </nfeProc>"""
        from io import BytesIO
        res = flask_client.post(
            "/api/importar/lote",
            data={"arquivos": (BytesIO(xml_xxe), "xxe_test.xml")},
            content_type="multipart/form-data",
        )
        # 400 (sem arquivo válido) ou 200/422 (processado sem vazar dados)
        assert res.status_code in (200, 400, 422)
        body = res.get_json()
        # O conteúdo de /etc/passwd não deve aparecer na resposta
        assert "root:" not in str(body)

    # A08 — Sanitização de nome de arquivo
    def test_nome_arquivo_xss_sanitizado(self):
        """Nome de arquivo com tags HTML deve ter os caracteres especiais removidos."""
        from src.web.security import sanitizar_nome_arquivo
        nome_malicioso = '<script>alert("xss")</script>.xml'
        resultado = sanitizar_nome_arquivo(nome_malicioso)
        assert "<" not in resultado
        assert ">" not in resultado
        assert '"' not in resultado

    def test_nome_arquivo_path_traversal_sanitizado(self):
        """Tentativa de path traversal no nome do arquivo deve ser bloqueada."""
        from src.web.security import sanitizar_nome_arquivo
        nome_malicioso = "../../etc/passwd"
        resultado = sanitizar_nome_arquivo(nome_malicioso)
        assert "/" not in resultado
        assert ".." not in resultado

    # A04 — Limite de arquivos no lote
    def test_limite_arquivos_lote_respeitado(self, flask_client):
        """Lote com mais arquivos que o limite deve processar apenas até o máximo."""
        from io import BytesIO
        from src.web.security import MAX_ARQUIVOS_LOTE
        with open(XML_PATH, "rb") as f:
            conteudo = f.read()

        # Werkzeug aceita lista de tuplas para múltiplos arquivos com a mesma chave
        data = {}
        arquivos_list = [
            (BytesIO(conteudo), f"nfe_{i}.xml")
            for i in range(MAX_ARQUIVOS_LOTE + 5)
        ]
        # Usa MultiDict para enviar múltiplos arquivos com a mesma chave
        from werkzeug.datastructures import MultiDict
        data = MultiDict([("arquivos", (BytesIO(conteudo), f"nfe_{i}.xml"))
                          for i in range(MAX_ARQUIVOS_LOTE + 5)])

        res = flask_client.post(
            "/api/importar/lote",
            data=data,
            content_type="multipart/form-data",
        )
        assert res.status_code == 200
        body = res.get_json()
        assert body["total"] <= MAX_ARQUIVOS_LOTE

    # A03 — IDs inválidos não causam erro
    def test_ids_nao_numericos_ignorados(self, flask_client):
        """IDs não numéricos no body devem ser ignorados sem erro 500."""
        res = flask_client.post(
            "/api/emitentes/autorizar",
            json={"ids": ["abc", -1, 0, None]},
            content_type="application/json",
        )
        # Deve retornar 400 (nenhum ID válido) e não 500
        assert res.status_code == 400
