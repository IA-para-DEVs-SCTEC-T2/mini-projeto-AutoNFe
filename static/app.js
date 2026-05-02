/**
 * AutoNFe — Frontend
 * Organizado em módulos: Api, Toast, Theme, Upload, Modal, Dashboard,
 * GerenciadorEntidade (genérico para Emitentes/Destinatários/Tributações).
 */

'use strict';

// ---------------------------------------------------------------------------
// Módulo: Utilitários DOM
// ---------------------------------------------------------------------------

const Dom = {
  get: (sel, ctx = document) => ctx.querySelector(sel),
  getAll: (sel, ctx = document) => [...ctx.querySelectorAll(sel)],
};

// ---------------------------------------------------------------------------
// Módulo: Formatação
// ---------------------------------------------------------------------------

const Fmt = {
  moeda: (valor, casas = 2) =>
    Number(valor).toLocaleString('pt-BR', {
      minimumFractionDigits: casas,
      maximumFractionDigits: casas,
    }),

  documento: (doc) => {
    if (!doc) return '—';
    const d = doc.replace(/\D/g, '');
    if (d.length === 14) return d.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
    if (d.length === 11) return d.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    return doc;
  },

  badgeValidacao: (ok) => {
    if (ok === null || ok === undefined) return '<span class="badge badge-blue">—</span>';
    return ok
      ? '<span class="badge badge-green">✓ OK</span>'
      : '<span class="badge badge-red">✗ Divergência</span>';
  },

  badgeStatus: (autorizado) =>
    autorizado
      ? '<span class="badge badge-green">Autorizado</span>'
      : '<span class="badge badge-amber">Pendente</span>',
};

// ---------------------------------------------------------------------------
// Módulo: API — todas as requisições incluem o token de autenticação
// ---------------------------------------------------------------------------

const Api = {
  // Token lido do meta tag injetado pelo servidor (ou variável de ambiente via template)
  _token: document.querySelector('meta[name="api-token"]')?.content || '',

  _headers(extra = {}) {
    return { 'X-API-Token': this._token, ...extra };
  },

  async get(url) {
    const res = await fetch(url, { headers: this._headers() });
    if (res.status === 401) { Toast.show('Sessão expirada. Recarregue a página.', 'error'); }
    return { ok: res.ok, data: await res.json() };
  },

  async post(url, body, isJson = true) {
    const opts = isJson
      ? {
          method: 'POST',
          headers: this._headers({ 'Content-Type': 'application/json' }),
          body: JSON.stringify(body),
        }
      : {
          method: 'POST',
          headers: this._headers(),
          body,
        };
    const res = await fetch(url, opts);
    if (res.status === 401) { Toast.show('Sessão expirada. Recarregue a página.', 'error'); }
    return { ok: res.ok, data: await res.json() };
  },
};

// ---------------------------------------------------------------------------
// Módulo: Toast
// ---------------------------------------------------------------------------

const Toast = {
  _el: null,
  _timer: null,

  init() {
    this._el = Dom.get('#toast');
  },

  show(msg, tipo = 'success') {
    clearTimeout(this._timer);
    this._el.textContent = msg;
    this._el.className = `toast toast-${tipo} show`;
    this._timer = setTimeout(() => this._el.classList.remove('show'), 3500);
  },
};

// ---------------------------------------------------------------------------
// Módulo: Tema
// ---------------------------------------------------------------------------

const Tema = {
  init() {
    if (localStorage.getItem('theme') === 'light') this._aplicar(true);
    Dom.get('#themeToggle').addEventListener('click', () => this._toggle());
    Dom.get('#mobileThemeBtn').addEventListener('click', () => this._toggle());
  },

  _toggle() {
    this._aplicar(!document.body.classList.contains('light'));
  },

  _aplicar(claro) {
    document.body.classList.toggle('light', claro);
    localStorage.setItem('theme', claro ? 'light' : 'dark');
  },
};

// ---------------------------------------------------------------------------
// Módulo: Sidebar / Navegação
// ---------------------------------------------------------------------------

const Navegacao = {
  _viewAtual: 'dashboard',
  _carregadores: {},

  init(carregadores) {
    this._carregadores = carregadores;

    Dom.getAll('.nav-item').forEach(btn =>
      btn.addEventListener('click', () => this.ir(btn.dataset.view))
    );

    Dom.getAll('.kpi-card.clickable').forEach(card =>
      card.addEventListener('click', () => this.ir(card.dataset.view, card.dataset.status))
    );

    Dom.get('#hamburger').addEventListener('click', () => this._toggleSidebar());
    Dom.get('#sidebarOverlay').addEventListener('click', () => this._fecharSidebar());
  },

  ir(nome, filtroStatus = null) {
    Dom.getAll('.view').forEach(v => v.classList.add('hidden'));
    Dom.getAll('.nav-item').forEach(n => n.classList.remove('active'));

    Dom.get(`#view-${nome}`)?.classList.remove('hidden');
    Dom.get(`.nav-item[data-view="${nome}"]`)?.classList.add('active');

    this._viewAtual = nome;
    this._fecharSidebar();

    const carregar = this._carregadores[nome];
    if (carregar) carregar(filtroStatus);
  },

  _toggleSidebar() {
    Dom.get('#sidebar').classList.toggle('open');
    Dom.get('#sidebarOverlay').classList.toggle('open');
  },

  _fecharSidebar() {
    Dom.get('#sidebar').classList.remove('open');
    Dom.get('#sidebarOverlay').classList.remove('open');
  },
};

// ---------------------------------------------------------------------------
// Módulo: Dashboard
// ---------------------------------------------------------------------------

const Dashboard = {
  async carregar() {
    const periodo = Dom.get('#dashPeriodo').value;
    const { ok, data } = await Api.get(`/api/dashboard?periodo=${periodo}`);
    if (!ok) return;

    this._atualizarKpis(data);
    this._atualizarSidebarStats(data);
    this._renderizarUltimasNotas(data.ultimas_nfe);
  },

  _atualizarKpis(data) {
    Dom.get('#kpiNfe').textContent = data.total_nfe;
    Dom.get('#kpiEmitPend').textContent = data.emitentes.pendentes;
    Dom.get('#kpiEmitAuth').textContent = `${data.emitentes.autorizados} autorizados`;
    Dom.get('#kpiDestPend').textContent = data.destinatarios.pendentes;
    Dom.get('#kpiDestAuth').textContent = `${data.destinatarios.autorizados} autorizados`;
    Dom.get('#kpiTribPend').textContent = data.tributacoes.pendentes;
    Dom.get('#kpiTribAuth').textContent = `${data.tributacoes.autorizados} autorizadas`;
  },

  _atualizarSidebarStats(data) {
    const totalPend = data.emitentes.pendentes + data.destinatarios.pendentes + data.tributacoes.pendentes;
    const totalAuth = data.emitentes.autorizados + data.destinatarios.autorizados + data.tributacoes.autorizados;
    Dom.get('#statNfe').textContent = data.total_nfe;
    Dom.get('#statPend').textContent = totalPend;
    Dom.get('#statAuth').textContent = totalAuth;
  },

  _renderizarUltimasNotas(notas) {
    const tbody = Dom.get('#tbodyUltimas');
    if (!notas.length) {
      tbody.innerHTML = '<tr><td colspan="7" class="empty-row">Nenhuma NF-e importada ainda.</td></tr>';
      return;
    }
    tbody.innerHTML = notas.map(n => `
      <tr>
        <td><strong>${n.numero_nf || '—'}</strong></td>
        <td>${n.serie || '—'}</td>
        <td>${n.emitente || '—'}</td>
        <td>${n.data_emissao?.substring(0, 10) ?? '—'}</td>
        <td>R$ ${Fmt.moeda(n.v_nf)}</td>
        <td>${Fmt.badgeValidacao(n.validacao_ok)}</td>
        <td>${n.importado_em}</td>
      </tr>
    `).join('');
  },

  init() {
    Dom.get('#dashPeriodo').addEventListener('change', () => this.carregar());
  },
};

// ---------------------------------------------------------------------------
// Módulo: NF-e Importadas
// ---------------------------------------------------------------------------

const NotasImportadas = {
  _dados: [],

  async carregar() {
    const { ok, data } = await Api.get('/api/notas');
    if (!ok) return;
    this._dados = data;
    this._renderizar(data);
  },

  _renderizar(lista) {
    const tbody = Dom.get('#tbodyNotas');
    if (!lista.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="empty-row">Nenhuma NF-e importada.</td></tr>';
      return;
    }
    tbody.innerHTML = lista.map(n => `
      <tr>
        <td><strong>${n.numero_nf || '—'}</strong></td>
        <td>${n.serie || '—'}</td>
        <td>${n.emitente || '—'}</td>
        <td>${n.destinatario || '—'}</td>
        <td>${n.data_emissao?.substring(0, 10) ?? '—'}</td>
        <td>R$ ${Fmt.moeda(n.v_nf)}</td>
        <td>${Fmt.badgeValidacao(n.validacao_ok)}</td>
        <td>
          <button class="btn-icon btn-icon-edit" onclick="ModalNota.abrir(${n.id})" title="Ver detalhes">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
          </button>
        </td>
      </tr>
    `).join('');
  },

  init() {
    Dom.get('#searchNotas').addEventListener('input', e => {
      const q = e.target.value.toLowerCase();
      this._renderizar(this._dados.filter(n =>
        (n.numero_nf || '').toLowerCase().includes(q) ||
        (n.emitente || '').toLowerCase().includes(q) ||
        (n.destinatario || '').toLowerCase().includes(q)
      ));
    });
  },
};

// ---------------------------------------------------------------------------
// Módulo: Modal de Detalhe NF-e
// ---------------------------------------------------------------------------

const ModalNota = {
  async abrir(id) {
    const { ok, data } = await Api.get(`/api/notas/${id}`);
    if (!ok) { Toast.show('Erro ao carregar NF-e.', 'error'); return; }

    Dom.get('#modalNotaTitulo').textContent = `NF-e ${data.numero_nf} / Série ${data.serie}`;
    Dom.get('#modalNotaConteudo').innerHTML = this._renderConteudo(data);
    Dom.get('#modalNota').classList.add('open');
  },

  fechar() {
    Dom.get('#modalNota').classList.remove('open');
  },

  _renderConteudo(data) {
    const t = data.totais;
    return `
      ${this._secaoIdentificacao(data)}
      ${this._secaoParte('Emitente', data.emitente)}
      ${this._secaoParte('Destinatário', data.destinatario)}
      ${this._secaoTotais(t)}
      ${data.itens.length ? this._secaoItens(data.itens) : ''}
    `;
  },

  _secaoIdentificacao(data) {
    return `
      <div class="modal-section">
        <h3>Identificação</h3>
        <div class="info-grid">
          <div class="info-item"><div class="info-label">Chave de Acesso</div>
            <div class="info-value" style="font-size:11px;word-break:break-all">${data.chave_acesso || '—'}</div></div>
          <div class="info-item"><div class="info-label">Natureza da Operação</div>
            <div class="info-value">${data.natureza_operacao || '—'}</div></div>
          <div class="info-item"><div class="info-label">Data Emissão</div>
            <div class="info-value">${data.data_emissao?.substring(0, 10) ?? '—'}</div></div>
          <div class="info-item"><div class="info-label">Tipo</div>
            <div class="info-value">${data.tipo_nf === '0' ? 'Entrada' : 'Saída'}</div></div>
          <div class="info-item"><div class="info-label">Validação</div>
            <div class="info-value">${Fmt.badgeValidacao(data.validacao_ok)}</div></div>
          ${data.validacao_erros ? `
            <div class="info-item" style="grid-column:1/-1">
              <div class="info-label">Divergências</div>
              <div class="info-value" style="color:var(--accent-red);font-size:12px">${data.validacao_erros}</div>
            </div>` : ''}
        </div>
      </div>`;
  },

  _secaoParte(titulo, parte) {
    return `
      <div class="modal-section">
        <h3>${titulo}</h3>
        <div class="info-grid">
          <div class="info-item"><div class="info-label">Nome</div><div class="info-value">${parte.nome || '—'}</div></div>
          <div class="info-item"><div class="info-label">CNPJ</div><div class="info-value">${Fmt.documento(parte.cnpj)}</div></div>
          <div class="info-item"><div class="info-label">Município/UF</div>
            <div class="info-value">${parte.municipio || '—'}/${parte.uf || '—'}</div></div>
        </div>
      </div>`;
  },

  _secaoTotais(t) {
    const campos = [
      ['Produtos', t.v_prod], ['Desconto', t.v_desc], ['Frete', t.v_frete],
      ['ICMS', t.v_icms], ['IPI', t.v_ipi], ['PIS', t.v_pis], ['COFINS', t.v_cofins],
    ];
    return `
      <div class="modal-section">
        <h3>Totais</h3>
        <div class="totais-grid">
          ${campos.map(([label, val]) => `
            <div class="total-item">
              <div class="total-label">${label}</div>
              <div class="total-value">R$ ${Fmt.moeda(val)}</div>
            </div>`).join('')}
          <div class="total-item total-nf">
            <div class="total-label">Total NF</div>
            <div class="total-value">R$ ${Fmt.moeda(t.v_nf)}</div>
          </div>
        </div>
      </div>`;
  },

  _secaoItens(itens) {
    return `
      <div class="modal-section">
        <h3>Itens (${itens.length})</h3>
        <div class="table-wrap" style="max-height:300px;overflow-y:auto">
          <table class="data-table">
            <thead>
              <tr><th>#</th><th>Código</th><th>Descrição</th><th>NCM</th><th>CFOP</th>
                  <th>Qtd</th><th>Vl Unit</th><th>Vl Total</th><th>CST</th><th>ICMS</th></tr>
            </thead>
            <tbody>
              ${itens.map(i => `
                <tr>
                  <td>${i.num_item}</td><td>${i.codigo || '—'}</td>
                  <td>${i.descricao || '—'}</td><td>${i.ncm || '—'}</td>
                  <td>${i.cfop || '—'}</td><td>${Fmt.moeda(i.quantidade, 3)}</td>
                  <td>R$ ${Fmt.moeda(i.valor_unitario)}</td>
                  <td>R$ ${Fmt.moeda(i.valor_total)}</td>
                  <td>${i.icms_cst || '—'}</td><td>R$ ${Fmt.moeda(i.icms_vicms)}</td>
                </tr>`).join('')}
            </tbody>
          </table>
        </div>
      </div>`;
  },

  init() {
    Dom.get('#btnFecharModal').addEventListener('click', () => this.fechar());
    Dom.get('#modalNota').addEventListener('click', e => {
      if (e.target === Dom.get('#modalNota')) this.fechar();
    });
  },
};

// ---------------------------------------------------------------------------
// Módulo: Modal de Detalhe Cadastro (Emitente / Destinatário)
// ---------------------------------------------------------------------------

const ModalCadastro = {
  async abrir(tipo, id) {
    const url = tipo === 'emitente' ? `/api/emitentes/${id}` : `/api/destinatarios/${id}`;
    const { ok, data } = await Api.get(url);
    if (!ok) { Toast.show('Erro ao carregar dados.', 'error'); return; }

    const titulo = tipo === 'emitente' ? `Emitente — ${data.nome}` : `Destinatário — ${data.nome}`;
    Dom.get('#modalCadastroTitulo').textContent = titulo;
    Dom.get('#modalCadastroConteudo').innerHTML = this._renderConteudo(data, tipo);
    Dom.get('#modalCadastro').classList.add('open');
  },

  fechar() {
    Dom.get('#modalCadastro').classList.remove('open');
  },

  _renderConteudo(d, tipo) {
    const doc = Fmt.documento(d.cnpj || d.cpf);
    const endereco = [d.logradouro, d.numero, d.complemento].filter(Boolean).join(', ');
    const bairro   = [d.bairro, d.municipio, d.uf].filter(Boolean).join(' / ');
    const cep      = d.cep ? d.cep.replace(/(\d{5})(\d{3})/, '$1-$2') : '—';

    const camposIdentificacao = [
      ['CNPJ/CPF', doc],
      ...(tipo === 'emitente' && d.ie   ? [['Inscrição Estadual', d.ie]]   : []),
      ...(tipo === 'emitente' && d.crt  ? [['Regime Tributário (CRT)', _crtLabel(d.crt)]] : []),
      ...(tipo === 'destinatario' && d.ie    ? [['Inscrição Estadual', d.ie]]    : []),
      ...(tipo === 'destinatario' && d.email ? [['E-mail', d.email]]             : []),
      ...(tipo === 'destinatario' && d.id_estrangeiro ? [['ID Estrangeiro', d.id_estrangeiro]] : []),
    ];

    return `
      <div class="modal-section">
        <h3>Identificação</h3>
        <div class="info-grid">
          <div class="info-item" style="grid-column:1/-1">
            <div class="info-label">Nome / Razão Social</div>
            <div class="info-value" style="font-size:16px">${d.nome || '—'}</div>
          </div>
          ${d.fantasia ? `
          <div class="info-item">
            <div class="info-label">Nome Fantasia</div>
            <div class="info-value">${d.fantasia}</div>
          </div>` : ''}
          ${camposIdentificacao.map(([label, val]) => `
          <div class="info-item">
            <div class="info-label">${label}</div>
            <div class="info-value">${val || '—'}</div>
          </div>`).join('')}
          <div class="info-item">
            <div class="info-label">Status</div>
            <div class="info-value">${Fmt.badgeStatus(d.autorizado)}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Cadastrado em</div>
            <div class="info-value">${d.criado_em || '—'}</div>
          </div>
          <div class="info-item">
            <div class="info-label">NF-e vinculadas</div>
            <div class="info-value">${d.total_notas ?? 0}</div>
          </div>
        </div>
      </div>

      <div class="modal-section">
        <h3>Endereço</h3>
        <div class="info-grid">
          ${endereco ? `
          <div class="info-item" style="grid-column:1/-1">
            <div class="info-label">Logradouro</div>
            <div class="info-value">${endereco}</div>
          </div>` : ''}
          <div class="info-item">
            <div class="info-label">Bairro / Município / UF</div>
            <div class="info-value">${bairro || '—'}</div>
          </div>
          <div class="info-item">
            <div class="info-label">CEP</div>
            <div class="info-value">${cep}</div>
          </div>
          ${d.fone ? `
          <div class="info-item">
            <div class="info-label">Telefone</div>
            <div class="info-value">${d.fone}</div>
          </div>` : ''}
        </div>
      </div>`;
  },

  init() {
    Dom.get('#btnFecharModalCadastro').addEventListener('click', () => this.fechar());
    Dom.get('#modalCadastro').addEventListener('click', e => {
      if (e.target === Dom.get('#modalCadastro')) this.fechar();
    });
  },
};

function _crtLabel(crt) {
  const labels = { '1': 'Simples Nacional', '2': 'Simples Nacional – excesso', '3': 'Regime Normal', '4': 'MEI' };
  return labels[crt] ? `${crt} – ${labels[crt]}` : crt;
}
// Elimina a triplicação de código para Emitentes, Destinatários e Tributações.
// ---------------------------------------------------------------------------

class GerenciadorEntidade {
  /**
   * @param {object} config
   * @param {string} config.nome          - Nome da entidade (ex: "emitentes")
   * @param {string} config.tbodyId       - ID do tbody da tabela
   * @param {string} config.searchId      - ID do input de busca
   * @param {string} config.filterId      - ID do select de filtro
   * @param {string} config.checkAllId    - ID do checkbox "marcar todos"
   * @param {string} config.checkClass    - Classe dos checkboxes individuais
   * @param {string} config.btnAutorizarId - ID do botão de autorizar
   * @param {number} config.colunas       - Número de colunas (para empty-row)
   * @param {function} config.renderLinha - Função (item) => string HTML da <tr>
   * @param {function} config.filtrarBusca - Função (item, query) => boolean
   * @param {string} config.msgVazia      - Mensagem quando lista vazia
   * @param {string} config.msgEntidade   - Nome para mensagem de autorização
   */
  constructor(config) {
    this._cfg = config;
    this._dados = [];
  }

  async carregar(filtroStatus = null) {
    const filtro = filtroStatus || Dom.get(`#${this._cfg.filterId}`)?.value || 'todos';
    if (filtroStatus) Dom.get(`#${this._cfg.filterId}`).value = filtroStatus;

    const { ok, data } = await Api.get(`/api/${this._cfg.nome}?status=${filtro}`);
    if (!ok) return;
    this._dados = data;
    this._renderizar(data);
  }

  _renderizar(lista) {
    const tbody = Dom.get(`#${this._cfg.tbodyId}`);
    if (!lista.length) {
      tbody.innerHTML = `<tr><td colspan="${this._cfg.colunas}" class="empty-row">${this._cfg.msgVazia}</td></tr>`;
      return;
    }
    tbody.innerHTML = lista.map(item => this._cfg.renderLinha(item)).join('');
  }

  async _autorizar() {
    const ids = Dom.getAll(`.${this._cfg.checkClass}:checked`).map(c => parseInt(c.value));
    if (!ids.length) {
      Toast.show(`Selecione ao menos um(a) ${this._cfg.msgEntidade}.`, 'info');
      return;
    }
    const { ok, data } = await Api.post(`/api/${this._cfg.nome}/autorizar`, { ids });
    if (ok) {
      Toast.show(data.mensagem);
      this.carregar();
    } else {
      Toast.show(data.erro || 'Erro ao autorizar.', 'error');
    }
  }

  init() {
    Dom.get(`#${this._cfg.filterId}`)?.addEventListener('change', () => this.carregar());

    Dom.get(`#${this._cfg.searchId}`)?.addEventListener('input', e => {
      const q = e.target.value.toLowerCase();
      this._renderizar(this._dados.filter(item => this._cfg.filtrarBusca(item, q)));
    });

    Dom.get(`#${this._cfg.checkAllId}`)?.addEventListener('change', e => {
      Dom.getAll(`.${this._cfg.checkClass}:not(:disabled)`).forEach(c => {
        c.checked = e.target.checked;
      });
    });

    Dom.get(`#${this._cfg.btnAutorizarId}`)?.addEventListener('click', () => this._autorizar());
  }
}

// ---------------------------------------------------------------------------
// Instâncias das entidades
// ---------------------------------------------------------------------------

const Emitentes = new GerenciadorEntidade({
  nome: 'emitentes',
  tbodyId: 'tbodyEmitentes',
  searchId: 'searchEmitentes',
  filterId: 'filterEmitentes',
  checkAllId: 'checkAllEmitentes',
  checkClass: 'check-emitente',
  btnAutorizarId: 'btnAutorizarEmitentes',
  colunas: 7,
  msgVazia: 'Nenhum emitente encontrado.',
  msgEntidade: 'emitente',
  renderLinha: (e) => `
    <tr>
      <td><input type="checkbox" class="check-emitente" value="${e.id}" ${e.autorizado ? 'disabled' : ''}/></td>
      <td>${Fmt.documento(e.cnpj || e.cpf)}</td>
      <td>
        <strong>${e.nome}</strong>
        ${e.fantasia ? `<br><span style="font-size:12px;color:var(--text-muted)">${e.fantasia}</span>` : ''}
      </td>
      <td>${e.municipio || '—'}/${e.uf || '—'}</td>
      <td>${Fmt.badgeStatus(e.autorizado)}</td>
      <td>${e.criado_em}</td>
      <td>
        <button class="btn-icon btn-icon-edit" onclick="ModalCadastro.abrir('emitente', ${e.id})" title="Ver detalhes">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </button>
      </td>
    </tr>`,
  filtrarBusca: (r, q) =>
    (r.nome || '').toLowerCase().includes(q) ||
    (r.cnpj || '').includes(q) ||
    (r.cpf || '').includes(q),
});

const Destinatarios = new GerenciadorEntidade({
  nome: 'destinatarios',
  tbodyId: 'tbodyDestinatarios',
  searchId: 'searchDestinatarios',
  filterId: 'filterDestinatarios',
  checkAllId: 'checkAllDestinatarios',
  checkClass: 'check-destinatario',
  btnAutorizarId: 'btnAutorizarDestinatarios',
  colunas: 7,
  msgVazia: 'Nenhum destinatário encontrado.',
  msgEntidade: 'destinatário',
  renderLinha: (d) => `
    <tr>
      <td><input type="checkbox" class="check-destinatario" value="${d.id}" ${d.autorizado ? 'disabled' : ''}/></td>
      <td>${Fmt.documento(d.cnpj || d.cpf)}</td>
      <td><strong>${d.nome}</strong></td>
      <td>${d.municipio || '—'}/${d.uf || '—'}</td>
      <td>${Fmt.badgeStatus(d.autorizado)}</td>
      <td>${d.criado_em}</td>
      <td>
        <button class="btn-icon btn-icon-edit" onclick="ModalCadastro.abrir('destinatario', ${d.id})" title="Ver detalhes">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
            <circle cx="12" cy="12" r="3"/>
          </svg>
        </button>
      </td>
    </tr>`,
  filtrarBusca: (r, q) =>
    (r.nome || '').toLowerCase().includes(q) ||
    (r.cnpj || '').includes(q),
});

const Tributacoes = new GerenciadorEntidade({
  nome: 'tributacoes',
  tbodyId: 'tbodyTributacoes',
  searchId: 'searchTributacoes',
  filterId: 'filterTributacoes',
  checkAllId: 'checkAllTributacoes',
  checkClass: 'check-tributacao',
  btnAutorizarId: 'btnAutorizarTributacoes',
  colunas: 8,
  msgVazia: 'Nenhuma tributação encontrada.',
  msgEntidade: 'tributação',
  renderLinha: (t) => `
    <tr>
      <td><input type="checkbox" class="check-tributacao" value="${t.id}" ${t.autorizado ? 'disabled' : ''}/></td>
      <td><span class="badge badge-blue">${t.cst_icms}</span></td>
      <td><strong>${t.cfop}</strong></td>
      <td>${t.descricao || '—'}</td>
      <td>${Fmt.moeda(t.aliq_icms)}%</td>
      <td>${Fmt.moeda(t.aliq_pis)}%</td>
      <td>${Fmt.moeda(t.aliq_cofins)}%</td>
      <td>${Fmt.badgeStatus(t.autorizado)}</td>
    </tr>`,
  filtrarBusca: (r, q) =>
    (r.cst_icms || '').includes(q) ||
    (r.cfop || '').includes(q) ||
    (r.descricao || '').toLowerCase().includes(q),
});

// ---------------------------------------------------------------------------
// Módulo: Upload — aceita um ou vários arquivos XML
// ---------------------------------------------------------------------------

const Upload = {
  init() {
    const area  = Dom.get('#uploadArea');
    const input = Dom.get('#fileInput');

    area.addEventListener('dragover', e => { e.preventDefault(); area.classList.add('drag-over'); });
    area.addEventListener('dragleave', () => area.classList.remove('drag-over'));
    area.addEventListener('drop', e => {
      e.preventDefault();
      area.classList.remove('drag-over');
      const files = [...e.dataTransfer.files].filter(f => f.name.toLowerCase().endsWith('.xml'));
      if (files.length) this._processar(files);
      else Toast.show('Nenhum arquivo .xml encontrado.', 'error');
    });

    input.addEventListener('change', e => {
      const files = [...e.target.files].filter(f => f.name.toLowerCase().endsWith('.xml'));
      if (files.length) this._processar(files);
      input.value = '';
    });
  },

  async _processar(files) {
    const resultDiv = Dom.get('#importResult');
    resultDiv.classList.remove('hidden');
    resultDiv.innerHTML = `
      <div class="lote-result-header">
        <h3><span class="spinner"></span> Processando ${files.length} arquivo(s)...</h3>
      </div>
      <div class="lote-progress-bar"><div class="lote-progress-fill" style="width:0%"></div></div>`;

    const formData = new FormData();
    files.forEach(f => formData.append('arquivos', f));

    const { ok, data } = await Api.post('/api/importar/lote', formData, false);

    if (!ok) {
      resultDiv.innerHTML = `<div style="padding:20px;color:var(--accent-red)">Erro: ${data.erro || 'Falha no servidor'}</div>`;
      Toast.show('Erro ao importar.', 'error');
      return;
    }

    resultDiv.innerHTML = this._htmlResultado(data);
    Toast.show(
      `Concluído: ${data.sucesso} importada(s)${data.erro ? `, ${data.erro} com erro` : ''}.`,
      data.erro === 0 ? 'success' : 'info'
    );

    // Atualiza os totalizadores da sidebar após qualquer importação
    if (data.sucesso > 0) Dashboard.carregar();
  },

  _htmlResultado(data) {
    const pct = data.total > 0 ? Math.round((data.sucesso / data.total) * 100) : 0;

    // Se foi só 1 arquivo, exibe resultado detalhado
    if (data.total === 1) {
      const item = data.itens[0];
      if (item.sucesso) {
        return `
          <div class="lote-result-header">
            <h3>✅ NF-e importada com sucesso</h3>
            <div class="lote-stats">
              <span class="lote-stat ok">✓ Validação: ${Fmt.badgeValidacao(item.validacao_ok)}</span>
            </div>
          </div>
          <div class="lote-progress-bar"><div class="lote-progress-fill" style="width:100%"></div></div>
          <div style="padding:16px 20px;display:flex;gap:32px;flex-wrap:wrap">
            <div><div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px">Arquivo</div>
              <div style="font-weight:600">${item.arquivo}</div></div>
            <div><div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px">Número NF</div>
              <div style="font-weight:600">${item.numero_nf || '—'}</div></div>
            <div><div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;margin-bottom:4px">Emitente</div>
              <div style="font-weight:600">${item.emitente || '—'}</div></div>
          </div>`;
      } else {
        const erros = (item.erros || ['Erro desconhecido']).join(' | ');
        return `
          <div class="lote-result-header" style="border-left:4px solid var(--accent-red)">
            <h3>❌ Erro na importação</h3>
          </div>
          <div style="padding:16px 20px;color:var(--accent-red)">${erros}</div>`;
      }
    }

    // Múltiplos arquivos — tabela resumo
    return `
      <div class="lote-result-header">
        <h3>Resultado da importação</h3>
        <div class="lote-stats">
          <span class="lote-stat tot">Total: ${data.total}</span>
          <span class="lote-stat ok">✓ ${data.sucesso} importadas</span>
          ${data.erro > 0 ? `<span class="lote-stat err">✗ ${data.erro} com erro</span>` : ''}
        </div>
      </div>
      <div class="lote-progress-bar">
        <div class="lote-progress-fill" style="width:${pct}%"></div>
      </div>
      <div style="overflow-x:auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>Arquivo</th><th>Número NF</th><th>Emitente</th>
              <th>Validação</th><th>Status / Motivo</th>
            </tr>
          </thead>
          <tbody>
            ${data.itens.map(i => `
              <tr>
                <td style="font-size:12px;color:var(--text-muted)">${i.arquivo}</td>
                <td><strong>${i.numero_nf || '—'}</strong></td>
                <td>${i.emitente || '—'}</td>
                <td>${Fmt.badgeValidacao(i.validacao_ok)}</td>
                <td>${i.sucesso
                  ? '<span class="badge badge-green">✓ OK</span>'
                  : `<div>
                      <span class="badge badge-red">✗ Erro</span>
                      <div style="font-size:12px;color:var(--accent-red);margin-top:4px;line-height:1.4">
                        ${(i.erros || ['Erro desconhecido']).join('<br>')}
                      </div>
                    </div>`
                }</td>
              </tr>`).join('')}
          </tbody>
        </table>
      </div>`;
  },
};

// ---------------------------------------------------------------------------
// Módulo: Usuários
// ---------------------------------------------------------------------------

const Usuarios = {
  _dados: [],

  async carregar() {
    const { ok, data } = await Api.get('/api/usuarios');
    if (!ok) { Dom.get('#tbodyUsuarios').innerHTML = '<tr><td colspan="6" class="empty-row">Sem permissão ou erro ao carregar.</td></tr>'; return; }
    this._dados = data;
    this._renderizar(data);
  },

  _renderizar(lista) {
    const tbody = Dom.get('#tbodyUsuarios');
    if (!lista.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="empty-row">Nenhum usuário cadastrado.</td></tr>';
      return;
    }
    tbody.innerHTML = lista.map(u => `
      <tr>
        <td><strong>${u.nome}</strong></td>
        <td>${u.email}</td>
        <td><span class="badge ${u.tipo === 'administrador' ? 'badge-blue' : 'badge-amber'}">${u.tipo === 'administrador' ? 'Administrador' : 'Padrão'}</span></td>
        <td>${u.ativo ? '<span class="badge badge-green">Ativo</span>' : '<span class="badge badge-red">Inativo</span>'}</td>
        <td>${u.criado_em}</td>
        <td>
          <button class="btn-icon btn-icon-edit" onclick="Usuarios.abrirEdicao(${u.id})" title="Editar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </button>
        </td>
      </tr>`).join('');
  },

  abrirNovo() {
    Dom.get('#modalUsuarioTitulo').textContent = 'Novo Usuário';
    Dom.get('usuarioId') && (Dom.get('#usuarioId').value = '');
    Dom.get('#usuarioNome').value = '';
    Dom.get('#usuarioEmail').value = '';
    Dom.get('#usuarioSenha').value = '';
    Dom.get('#usuarioTipo').value = 'padrao';
    Dom.get('#usuarioAtivo').value = 'true';
    Dom.get('#grupoSenha').style.display = '';
    Dom.get('#grupoAtivo').style.display = 'none';
    Dom.get('#reqSenhaModal').innerHTML = '';
    Dom.get('#modalUsuario').classList.add('open');
  },

  abrirEdicao(id) {
    const u = this._dados.find(x => x.id === id);
    if (!u) return;
    Dom.get('#modalUsuarioTitulo').textContent = 'Editar Usuário';
    Dom.get('#usuarioId').value  = u.id;
    Dom.get('#usuarioNome').value  = u.nome;
    Dom.get('#usuarioEmail').value = u.email;
    Dom.get('#usuarioSenha').value = '';
    Dom.get('#usuarioTipo').value  = u.tipo;
    Dom.get('#usuarioAtivo').value = u.ativo ? 'true' : 'false';
    Dom.get('#grupoSenha').style.display = '';
    Dom.get('#grupoAtivo').style.display = '';
    Dom.get('#reqSenhaModal').innerHTML = '';
    Dom.get('#modalUsuario').classList.add('open');
  },

  fecharModal() {
    Dom.get('#modalUsuario').classList.remove('open');
  },

  async salvar(e) {
    e.preventDefault();
    const id    = Dom.get('#usuarioId').value;
    const body  = {
      nome:  Dom.get('#usuarioNome').value.trim(),
      email: Dom.get('#usuarioEmail').value.trim(),
      tipo:  Dom.get('#usuarioTipo').value,
      ativo: Dom.get('#usuarioAtivo').value === 'true',
    };
    const senha = Dom.get('#usuarioSenha').value;
    if (senha) body.senha = senha;

    const url    = id ? `/api/usuarios/${id}` : '/api/usuarios';
    const method = id ? 'PUT' : 'POST';
    const res    = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json', 'X-API-Token': Api._token },
      body: JSON.stringify(body),
    });
    const data = await res.json();

    if (res.ok) {
      Toast.show(data.mensagem || 'Salvo com sucesso.');
      this.fecharModal();
      this.carregar();
    } else {
      Toast.show(data.erro || 'Erro ao salvar.', 'error');
    }
  },

  init() {
    Dom.get('#btnNovoUsuario')?.addEventListener('click', () => this.abrirNovo());
    Dom.get('#btnFecharModalUsuario')?.addEventListener('click', () => this.fecharModal());
    Dom.get('#btnCancelarUsuario')?.addEventListener('click', () => this.fecharModal());
    Dom.get('#modalUsuario')?.addEventListener('click', e => {
      if (e.target === Dom.get('#modalUsuario')) this.fecharModal();
    });
    Dom.get('#formUsuario')?.addEventListener('submit', e => this.salvar(e));
    Dom.get('#usuarioSenha')?.addEventListener('input', e => validarRequisitosModal(e.target.value));
    Dom.get('#searchUsuarios')?.addEventListener('input', e => {
      const q = e.target.value.toLowerCase();
      this._renderizar(this._dados.filter(u =>
        u.nome.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
      ));
    });
  },
};

// ---------------------------------------------------------------------------
// Inicialização
// ---------------------------------------------------------------------------

Toast.init();
Tema.init();
Dashboard.init();
NotasImportadas.init();
ModalNota.init();
ModalCadastro.init();
Upload.init();
Emitentes.init();
Destinatarios.init();
Tributacoes.init();
Usuarios.init();

Navegacao.init({
  dashboard:     () => Dashboard.carregar(),
  notas:         () => NotasImportadas.carregar(),
  emitentes:     (f) => Emitentes.carregar(f),
  destinatarios: (f) => Destinatarios.carregar(f),
  tributacoes:   (f) => Tributacoes.carregar(f),
  usuarios:      () => Usuarios.carregar(),
  importar:      () => {},
});

Navegacao.ir('dashboard');
