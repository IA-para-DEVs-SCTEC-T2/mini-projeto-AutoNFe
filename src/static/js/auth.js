'use strict';

/* ── Mostrar/ocultar senha ── */
function toggleSenha(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const visivel = input.type === 'text';
  input.type = visivel ? 'password' : 'text';
  btn.style.color = visivel ? '' : 'var(--emerald-400)';
}

/* ── Validação visual dos requisitos de senha ── */
const REQUISITOS = [
  { id: 'req-min',   regex: /.{8,}/,                          label: 'Mínimo 8 caracteres' },
  { id: 'req-lower', regex: /[a-z]/,                          label: 'Letra minúscula' },
  { id: 'req-upper', regex: /[A-Z]/,                          label: 'Letra maiúscula' },
  { id: 'req-num',   regex: /\d/,                             label: 'Número' },
  { id: 'req-esp',   regex: /[!@#$%^&*()\-_=+\[\]{};':"\\|,.<>/?]/, label: 'Caractere especial (!@#$%)' },
];

function validarRequisitos(senha) {
  REQUISITOS.forEach(r => {
    const el = document.getElementById(r.id);
    if (!el) return;
    const ok = r.regex.test(senha);
    el.classList.toggle('ok', ok);
    el.classList.toggle('erro', !ok && senha.length > 0);
  });
}

/* ── Requisitos dinâmicos no modal de usuário ── */
function validarRequisitosModal(senha) {
  const lista = document.getElementById('reqSenhaModal');
  if (!lista) return;
  lista.innerHTML = REQUISITOS.map(r => {
    const ok = r.regex.test(senha);
    const cls = senha.length === 0 ? '' : (ok ? 'ok' : 'erro');
    return `<li class="req ${cls}">${r.label}</li>`;
  }).join('');
}
