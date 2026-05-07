"""
Aplicação Flask – Backend do AutoNFe
Ponto de entrada: python main.py
"""

from __future__ import annotations

import os
import secrets
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

# ---------------------------------------------------------------------------
# Carrega variáveis do .env se existir (sem dependência externa)
# ---------------------------------------------------------------------------

_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for _linha in _env_path.read_text(encoding="utf-8").splitlines():
        _linha = _linha.strip()
        if _linha and not _linha.startswith("#") and "=" in _linha:
            _chave, _, _valor = _linha.partition("=")
            os.environ.setdefault(_chave.strip(), _valor.strip())

from src.agents.orquestrador import Orquestrador
from src.web.auth import (
    admin_requerido,
    autenticar_usuario,
    gerar_senha_temporaria,
    login_requerido,
    seed_admin,
    validar_senha_forte,
)
from src.database.models import Usuario, criar_tabelas
from src.database.repository import (
    autorizar_destinatarios,
    autorizar_emitentes,
    autorizar_tributacoes,
    buscar_destinatario_por_id,
    buscar_emitente_por_id,
    buscar_nota_por_id,
    contar_destinatarios,
    contar_emitentes,
    contar_notas_desde,
    contar_tributacoes,
    listar_destinatarios,
    listar_emitentes,
    listar_notas,
    listar_tributacoes,
    sessao_db,
    ultimas_notas,
)
from src.database.serializers import (
    serializar_destinatario,
    serializar_destinatario_detalhe,
    serializar_emitente,
    serializar_emitente_detalhe,
    serializar_nota_dashboard,
    serializar_nota_detalhe,
    serializar_nota_resumo,
    serializar_tributacao,
)
from src.web.security import (
    MAX_ARQUIVOS_LOTE,
    _API_TOKEN,
    configurar_logging,
    log_autorizacao,
    log_importacao,
    registrar_headers_seguranca,
    requer_autenticacao,
    sanitizar_nome_arquivo,
)

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

configurar_logging()

_ROOT = Path(__file__).parent.parent.parent  # raiz do projeto

app = Flask(
    __name__,
    template_folder=str(_ROOT / "templates"),
    static_folder=str(_ROOT / "static"),
)

# A05 — SECRET_KEY via variável de ambiente; nunca hardcoded
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

# A04 — Limite de upload reduzido para 50 MB (suficiente para lotes reais)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

# A05 — Headers de segurança em todas as respostas
registrar_headers_seguranca(app)

criar_tabelas()
seed_admin()  # garante usuário admin inicial

_PERIODOS = {
    "dia": lambda hoje: hoje.replace(hour=0, minute=0, second=0, microsecond=0),
    "mes": lambda hoje: hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
    "ano": lambda hoje: hoje.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
}

# Valores permitidos para o parâmetro período (whitelist)
_PERIODOS_VALIDOS = frozenset(_PERIODOS.keys())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _data_inicio_periodo(periodo: str) -> datetime:
    """Retorna o datetime de início do período. Usa 'mes' como fallback seguro."""
    hoje = datetime.now()
    # A01 — whitelist de valores aceitos; ignora valores arbitrários
    calcular = _PERIODOS.get(periodo if periodo in _PERIODOS_VALIDOS else "mes")
    return calcular(hoje)


def _ids_do_body() -> list[int]:
    """Extrai e valida a lista de IDs do corpo JSON. Aceita apenas inteiros positivos."""
    payload = request.get_json(silent=True) or {}
    ids_raw = payload.get("ids", [])
    if not isinstance(ids_raw, list):
        return []
    # A03 — valida que cada item é inteiro positivo antes de usar
    return [int(i) for i in ids_raw if str(i).isdigit() and int(i) > 0]


def _resposta_autorizacao(quantidade: int, entidade: str) -> tuple:
    if quantidade == 0:
        return jsonify({"erro": "Nenhum registro encontrado para autorizar."}), 404
    return jsonify({"mensagem": f"{quantidade} {entidade} autorizado(s)."})


# ---------------------------------------------------------------------------
# Autenticação — Login / Logout / Troca de senha / Recuperação
# ---------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if "usuario_id" in session:
        return redirect(url_for("index"))
    erro = info = login_val = None
    if request.method == "POST":
        login_val = request.form.get("login", "").strip()
        senha = request.form.get("senha", "")
        usuario, motivo = autenticar_usuario(login_val, senha)
        if not usuario:
            erro = motivo
        else:
            usando_temp = bool(
                usuario.senha_temp
                and check_password_hash(usuario.senha_temp, senha)
            )
            session["usuario_id"]   = usuario.id
            session["usuario_nome"] = usuario.nome
            session["usuario_tipo"] = usuario.tipo
            session["usando_temp"]  = usando_temp
            if usuario.trocar_senha or usando_temp:
                return redirect(url_for("trocar_senha"))
            return redirect(url_for("index"))
    return render_template("login.html", erro=erro, info=info, login_val=login_val)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/trocar-senha", methods=["GET", "POST"])
def trocar_senha():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    usando_temp    = session.get("usando_temp", False)
    primeiro_login = not usando_temp
    erro = None
    if request.method == "POST":
        nova_senha  = request.form.get("nova_senha", "")
        confirmar   = request.form.get("confirmar_senha", "")
        senha_atual = request.form.get("senha_atual", "")
        erros_senha = validar_senha_forte(nova_senha)
        if erros_senha:
            erro = "Senha fraca: " + "; ".join(erros_senha)
        elif nova_senha != confirmar:
            erro = "As senhas não coincidem."
        else:
            with sessao_db() as db:
                usuario = db.query(Usuario).filter_by(id=session["usuario_id"]).first()
                if not usuario:
                    return redirect(url_for("login"))
                if usando_temp:
                    if not usuario.senha_temp or not check_password_hash(usuario.senha_temp, senha_atual):
                        erro = "Senha temporária incorreta."
                    else:
                        usuario.senha_hash   = generate_password_hash(nova_senha)
                        usuario.senha_temp   = None
                        usuario.trocar_senha = False
                        db.commit()
                        session.pop("usando_temp", None)
                        return redirect(url_for("index"))
                else:
                    usuario.senha_hash   = generate_password_hash(nova_senha)
                    usuario.trocar_senha = False
                    db.commit()
                    return redirect(url_for("index"))
    return render_template("trocar_senha.html", erro=erro, usar_temp=usando_temp, primeiro_login=primeiro_login)


@app.route("/esqueci-senha", methods=["GET", "POST"])
def esqueci_senha():
    import logging as _log
    erro = sucesso = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        with sessao_db() as db:
            usuario = db.query(Usuario).filter_by(email=email).first()
        if not usuario or not usuario.ativo:
            sucesso = "Se o e-mail estiver cadastrado, você receberá a senha temporária. Verifique também a pasta de spam."
        else:
            senha_temp = gerar_senha_temporaria()
            with sessao_db() as db:
                u = db.query(Usuario).filter_by(id=usuario.id).first()
                u.senha_temp   = generate_password_hash(senha_temp)
                u.trocar_senha = True
                db.commit()
            _log.getLogger("autonfe.auth").warning(
                "SENHA TEMPORÁRIA para %s: %s  (configure SMTP para envio real)", email, senha_temp
            )
            sucesso = (
                f"Senha temporária gerada. Em produção seria enviada para {email}. "
                "Neste ambiente, consulte o log do servidor."
            )
    return render_template("esqueci_senha.html", erro=erro, sucesso=sucesso)


# ---------------------------------------------------------------------------
# Página principal — exige login
# ---------------------------------------------------------------------------

@app.route("/")
@login_requerido
def index():
    # Injeta o token no template para que o JS possa autenticar as chamadas API
    return render_template("index.html", api_token=_API_TOKEN)


# ---------------------------------------------------------------------------
# Importação de NF-e — arquivo único
# ---------------------------------------------------------------------------

@app.route("/api/importar", methods=["POST"])
@requer_autenticacao
def importar_nfe():
    """Recebe um arquivo XML via multipart/form-data e processa os 3 agentes."""
    if "arquivo" not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado."}), 400

    arquivo = request.files["arquivo"]
    nome_seguro = sanitizar_nome_arquivo(arquivo.filename or "")

    if not nome_seguro.lower().endswith(".xml"):
        return jsonify({"erro": "Apenas arquivos XML são aceitos."}), 400

    with sessao_db() as db:
        resultado = Orquestrador(db).processar_bytes(arquivo.read())

    log_importacao(nome_seguro, resultado.sucesso, request.remote_addr)

    resposta = _montar_resposta_importacao(resultado)
    status_code = 200 if resultado.sucesso else 422
    return jsonify(resposta), status_code


# ---------------------------------------------------------------------------
# Importação em lote — múltiplos arquivos enviados pelo browser
# ---------------------------------------------------------------------------

@app.route("/api/importar/lote", methods=["POST"])
@requer_autenticacao
def importar_lote():
    """Recebe múltiplos arquivos XML e processa cada um, retornando resumo."""
    arquivos = request.files.getlist("arquivos")
    if not arquivos:
        return jsonify({"erro": "Nenhum arquivo enviado."}), 400

    # A04 — limita quantidade de arquivos por lote
    xmls = [
        a for a in arquivos
        if sanitizar_nome_arquivo(a.filename or "").lower().endswith(".xml")
    ][:MAX_ARQUIVOS_LOTE]

    if not xmls:
        return jsonify({"erro": "Nenhum arquivo .xml encontrado no envio."}), 400

    resultados = []
    with sessao_db() as db:
        orq = Orquestrador(db)
        for arquivo in xmls:
            nome_seguro = sanitizar_nome_arquivo(arquivo.filename or "")
            res = orq.processar_bytes(arquivo.read())
            log_importacao(nome_seguro, res.sucesso, request.remote_addr)
            resultados.append(_resumo_lote(nome_seguro, res))

    return jsonify({
        "total": len(resultados),
        "sucesso": sum(1 for r in resultados if r["sucesso"]),
        "erro": sum(1 for r in resultados if not r["sucesso"]),
        "itens": resultados,
    })


def _montar_resposta_importacao(resultado) -> dict:
    """Constrói o dicionário de resposta da importação sem lógica inline."""
    resposta = {
        "sucesso": resultado.sucesso,
        "nota_id": resultado.nota_id,
        "erros": resultado.erros,
    }

    if resultado.leitura:
        resposta.update({
            "chave_acesso": resultado.leitura.chave_acesso,
            "numero_nf": resultado.leitura.numero_nf,
            "emitente": resultado.leitura.emitente.nome,
        })

    if resultado.cadastro:
        cad = resultado.cadastro
        resposta["cadastro"] = {
            "emitente": _status_cadastro(cad.emitente),
            "destinatario": _status_cadastro(cad.destinatario),
            "tributacoes_novas": sum(1 for t in cad.tributacoes if t.acao == "cadastrado"),
        }

    if resultado.validacao:
        val = resultado.validacao
        resposta["validacao"] = {
            "ok": val.ok,
            "divergencias": len(val.diferencas_itens) + len(val.diferencas_totais),
        }

    return resposta


def _status_cadastro(status) -> dict:
    if not status:
        return {"acao": None, "autorizado": None}
    return {"acao": status.acao, "autorizado": status.autorizado}


def _resumo_lote(nome_arquivo: str, resultado) -> dict:
    """Resumo compacto de um item do lote. nome_arquivo já sanitizado."""
    item = {
        "arquivo": nome_arquivo,
        "sucesso": resultado.sucesso,
        "erros": resultado.erros,
        "numero_nf": None,
        "emitente": None,
        "validacao_ok": None,
    }
    if resultado.leitura:
        item["numero_nf"] = resultado.leitura.numero_nf
        item["emitente"] = resultado.leitura.emitente.nome
    if resultado.validacao:
        item["validacao_ok"] = resultado.validacao.ok
    return item


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route("/api/dashboard")
@requer_autenticacao
def dashboard():
    periodo = request.args.get("periodo", "mes")
    data_inicio = _data_inicio_periodo(periodo)

    with sessao_db() as db:
        return jsonify({
            "periodo": periodo,
            "total_nfe": contar_notas_desde(db, data_inicio),
            "emitentes": contar_emitentes(db),
            "destinatarios": contar_destinatarios(db),
            "tributacoes": contar_tributacoes(db),
            "ultimas_nfe": [serializar_nota_dashboard(n) for n in ultimas_notas(db)],
        })


# ---------------------------------------------------------------------------
# Emitentes
# ---------------------------------------------------------------------------

@app.route("/api/emitentes")
@requer_autenticacao
def rota_listar_emitentes():
    status = request.args.get("status", "todos")
    with sessao_db() as db:
        return jsonify([serializar_emitente(e) for e in listar_emitentes(db, status)])


@app.route("/api/emitentes/autorizar", methods=["POST"])
@requer_autenticacao
def rota_autorizar_emitentes():
    ids = _ids_do_body()
    if not ids:
        return jsonify({"erro": "Nenhum ID informado."}), 400
    log_autorizacao("emitente", ids, request.remote_addr)
    with sessao_db() as db:
        qtd = autorizar_emitentes(db, ids)
    return _resposta_autorizacao(qtd, "emitente(s)")


@app.route("/api/emitentes/<int:emitente_id>")
@requer_autenticacao
def rota_detalhe_emitente(emitente_id: int):
    with sessao_db() as db:
        emitente = buscar_emitente_por_id(db, emitente_id)
        if not emitente:
            return jsonify({"erro": "Emitente não encontrado."}), 404
        return jsonify(serializar_emitente_detalhe(emitente))


# ---------------------------------------------------------------------------
# Destinatários
# ---------------------------------------------------------------------------

@app.route("/api/destinatarios")
@requer_autenticacao
def rota_listar_destinatarios():
    status = request.args.get("status", "todos")
    with sessao_db() as db:
        return jsonify([serializar_destinatario(d) for d in listar_destinatarios(db, status)])


@app.route("/api/destinatarios/autorizar", methods=["POST"])
@requer_autenticacao
def rota_autorizar_destinatarios():
    ids = _ids_do_body()
    if not ids:
        return jsonify({"erro": "Nenhum ID informado."}), 400
    log_autorizacao("destinatario", ids, request.remote_addr)
    with sessao_db() as db:
        qtd = autorizar_destinatarios(db, ids)
    return _resposta_autorizacao(qtd, "destinatário(s)")


@app.route("/api/destinatarios/<int:destinatario_id>")
@requer_autenticacao
def rota_detalhe_destinatario(destinatario_id: int):
    with sessao_db() as db:
        destinatario = buscar_destinatario_por_id(db, destinatario_id)
        if not destinatario:
            return jsonify({"erro": "Destinatário não encontrado."}), 404
        return jsonify(serializar_destinatario_detalhe(destinatario))


# ---------------------------------------------------------------------------
# Tributações
# ---------------------------------------------------------------------------

@app.route("/api/tributacoes")
@requer_autenticacao
def rota_listar_tributacoes():
    status = request.args.get("status", "todos")
    with sessao_db() as db:
        return jsonify([serializar_tributacao(t) for t in listar_tributacoes(db, status)])


@app.route("/api/tributacoes/autorizar", methods=["POST"])
@requer_autenticacao
def rota_autorizar_tributacoes():
    ids = _ids_do_body()
    if not ids:
        return jsonify({"erro": "Nenhum ID informado."}), 400
    log_autorizacao("tributacao", ids, request.remote_addr)
    with sessao_db() as db:
        qtd = autorizar_tributacoes(db, ids)
    return _resposta_autorizacao(qtd, "tributação(ões)")


# ---------------------------------------------------------------------------
# NF-e importadas
# ---------------------------------------------------------------------------

@app.route("/api/notas")
@requer_autenticacao
def rota_listar_notas():
    with sessao_db() as db:
        return jsonify([serializar_nota_resumo(n) for n in listar_notas(db)])


@app.route("/api/notas/<int:nota_id>")
@requer_autenticacao
def rota_detalhe_nota(nota_id: int):
    with sessao_db() as db:
        nota = buscar_nota_por_id(db, nota_id)
        if not nota:
            return jsonify({"erro": "NF-e não encontrada."}), 404
        return jsonify(serializar_nota_detalhe(nota))


# ---------------------------------------------------------------------------
# API: Usuários (somente administrador)
# ---------------------------------------------------------------------------

@app.route("/api/usuarios")
@login_requerido
@admin_requerido
def rota_listar_usuarios():
    with sessao_db() as db:
        usuarios = db.query(Usuario).order_by(Usuario.nome).all()
        return jsonify([{
            "id": u.id,
            "nome": u.nome,
            "email": u.email,
            "tipo": u.tipo,
            "ativo": u.ativo,
            "trocar_senha": u.trocar_senha,
            "criado_em": u.criado_em.strftime("%d/%m/%Y") if u.criado_em else "",
        } for u in usuarios])


@app.route("/api/usuarios", methods=["POST"])
@login_requerido
@admin_requerido
def rota_criar_usuario():
    data = request.get_json(silent=True) or {}
    nome   = (data.get("nome") or "").strip()
    email  = (data.get("email") or "").strip().lower()
    senha  = data.get("senha") or ""
    tipo   = data.get("tipo") or "padrao"

    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, e-mail e senha são obrigatórios."}), 400

    erros = validar_senha_forte(senha)
    if erros:
        return jsonify({"erro": "Senha fraca: " + "; ".join(erros)}), 400

    if tipo not in ("padrao", "administrador"):
        tipo = "padrao"

    with sessao_db() as db:
        if db.query(Usuario).filter_by(email=email).first():
            return jsonify({"erro": "E-mail já cadastrado."}), 409
        novo = Usuario(
            nome=nome,
            email=email,
            senha_hash=generate_password_hash(senha),
            tipo=tipo,
            ativo=True,
            trocar_senha=True,  # força troca de senha no primeiro login
        )
        db.add(novo)
        db.commit()
        return jsonify({"mensagem": "Usuário criado com sucesso.", "id": novo.id}), 201


@app.route("/api/usuarios/<int:usuario_id>", methods=["PUT"])
@login_requerido
@admin_requerido
def rota_atualizar_usuario(usuario_id: int):
    data = request.get_json(silent=True) or {}
    with sessao_db() as db:
        usuario = db.query(Usuario).filter_by(id=usuario_id).first()
        if not usuario:
            return jsonify({"erro": "Usuário não encontrado."}), 404

        if "nome" in data and data["nome"].strip():
            usuario.nome = data["nome"].strip()
        if "email" in data and data["email"].strip():
            novo_email = data["email"].strip().lower()
            existente = db.query(Usuario).filter_by(email=novo_email).first()
            if existente and existente.id != usuario_id:
                return jsonify({"erro": "E-mail já em uso por outro usuário."}), 409
            usuario.email = novo_email
        if "tipo" in data and data["tipo"] in ("padrao", "administrador"):
            usuario.tipo = data["tipo"]
        if "ativo" in data:
            usuario.ativo = bool(data["ativo"])
        if "senha" in data and data["senha"]:
            erros = validar_senha_forte(data["senha"])
            if erros:
                return jsonify({"erro": "Senha fraca: " + "; ".join(erros)}), 400
            usuario.senha_hash   = generate_password_hash(data["senha"])
            usuario.trocar_senha = False

        db.commit()
        return jsonify({"mensagem": "Usuário atualizado com sucesso."})


# ---------------------------------------------------------------------------
# Entry point — A05: debug desabilitado por padrão, host restrito
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    host = os.environ.get("FLASK_HOST", "127.0.0.1")  # apenas localhost por padrão
    port = int(os.environ.get("FLASK_PORT", "5000"))
    app.run(debug=debug_mode, host=host, port=port)
