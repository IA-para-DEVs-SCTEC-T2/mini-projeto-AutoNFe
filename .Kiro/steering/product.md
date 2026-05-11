# Visão do Produto — AutoNFe

## 1. Visão Geral do Produto

O **AutoNFe** é um sistema multi-agente para automação do processamento de Notas Fiscais Eletrônicas (NF-e). Ele recebe arquivos XML de NF-e já emitidas ou recebidas de fornecedores, extrai os dados fiscais de forma estruturada, cadastra automaticamente as entidades envolvidas (emitente, destinatário e tributações) e valida a integridade matemática dos valores declarados.

**Problema que resolve:** o processo manual de digitação e conferência de dados de NF-e é lento, sujeito a erros humanos e gera retrabalho. O AutoNFe elimina esse esforço ao automatizar a leitura, o cadastro e a validação, deixando para o usuário apenas a decisão de autorizar os registros gerados.

---

## 2. Público-Alvo

| Perfil | Descrição |
|---|---|
| **Operador fiscal** | Responsável por importar os XMLs de NF-e recebidos ou emitidos, acompanhar o dashboard e autorizar os cadastros pendentes |
| **Administrador do sistema** | Gerencia usuários, define permissões e monitora o uso da plataforma |

O sistema é voltado para pequenas e médias empresas que lidam com volume relevante de NF-e e precisam de uma solução local, simples e sem dependência de serviços externos.

---

## 3. Recursos Principais

### Importação de NF-e
- Upload de arquivo XML único via interface web
- Importação em lote (até 50 arquivos por vez)
- Suporte ao padrão NF-e v4.00 (schema `leiauteNFe_v4.00.xsd`)
- Rejeição de duplicatas por chave de acesso

### Pipeline de Agentes
- **Agente 1 — Leitura:** extrai emitente, destinatário, produtos, tributação e totalizadores do XML
- **Agente 2 — Cadastro:** verifica e cadastra automaticamente emitentes, destinatários e tributações com status pendente
- **Agente 3 — Validação:** confere Base × Alíquota por imposto (ICMS, IPI, PIS, COFINS) e valida os totalizadores da NF-e

### Dashboard
- Visão consolidada de NF-e importadas com filtros por dia, mês e ano
- Contadores de emitentes, destinatários e tributações (total e pendentes)
- Lista das últimas NF-e importadas

### Autorização de Cadastros
- Fluxo de aprovação para registros criados automaticamente pelo Agente 2
- Seleção individual ou em lote para autorização
- Registros permanecem com status **pendente** até aprovação explícita do usuário

### Autenticação e Gestão de Usuários
- Login por e-mail ou nome de usuário
- Senhas com hash bcrypt — nunca armazenadas em texto claro
- Requisitos de senha forte (mínimo 8 caracteres, maiúscula, minúscula, número e caractere especial)
- Troca de senha obrigatória no primeiro login
- Recuperação de senha via senha temporária
- Cadastro de usuários com perfis: **Padrão** e **Administrador**

### Segurança
- Autenticação obrigatória em todas as rotas (sessão + token de API)
- Headers HTTP de segurança (CSP, X-Frame-Options, X-XSS-Protection)
- Parser XML com proteção contra XXE
- Sanitização de nomes de arquivo (anti-XSS e path traversal)
- Logging de auditoria de importações, autorizações e acessos negados

---

## 4. Objetivos de Negócio

| Objetivo | Descrição |
|---|---|
| **Reduzir retrabalho manual** | Eliminar a digitação de dados de NF-e, substituindo por importação automatizada via XML |
| **Garantir integridade fiscal** | Validar matematicamente os valores declarados no XML antes de qualquer cadastro definitivo |
| **Controle de cadastros** | Nenhum emitente, destinatário ou tributação é ativado sem aprovação explícita do usuário — evita cadastros incorretos |
| **Rastreabilidade** | Toda importação, autorização e acesso negado é registrado em log de auditoria |
| **Simplicidade operacional** | Sistema local, sem dependência de cloud ou serviços externos — instalação com `pip install` e execução com `python main.py` |
| **Segurança por padrão** | Aplicação das diretrizes OWASP Top 10 desde a concepção, não como adição posterior |

---

## 5. Casos de Uso

### UC-01 — Importar uma NF-e
**Como** operador fiscal,
**quero** fazer upload de um arquivo XML de NF-e,
**para que** os dados sejam extraídos, cadastrados e validados automaticamente sem digitação manual.

**Fluxo principal:**
1. Operador acessa o dashboard e clica em "Importar NF-e"
2. Seleciona o arquivo XML
3. O sistema executa o pipeline: Agente 1 (leitura) → Agente 2 (cadastro) → Agente 3 (validação)
4. O resultado é exibido: dados extraídos, entidades cadastradas e resultado da validação
5. Emitente, destinatário e tributações ficam com status **pendente** aguardando autorização

**Exceções:**
- XML inválido ou fora do padrão NF-e v4.00 → erro descritivo exibido ao usuário
- NF-e já importada (chave de acesso duplicada) → importação rejeitada com aviso

---

### UC-02 — Importar NF-e em lote
**Como** operador fiscal,
**quero** enviar múltiplos arquivos XML de uma vez,
**para que** eu possa processar um volume maior de notas sem repetir o processo individualmente.

**Fluxo principal:**
1. Operador seleciona até 50 arquivos XML
2. O sistema processa cada arquivo pelo pipeline de agentes
3. Um resumo é exibido: total processado, sucessos e erros por arquivo

---

### UC-03 — Autorizar cadastros pendentes
**Como** operador fiscal,
**quero** revisar e autorizar os emitentes, destinatários e tributações cadastrados automaticamente,
**para que** apenas registros validados por mim sejam considerados ativos no sistema.

**Fluxo principal:**
1. No dashboard, operador clica no contador de pendentes (emitentes, destinatários ou tributações)
2. A lista de registros com status **pendente** é exibida
3. Operador seleciona um ou mais registros e confirma a autorização
4. Registros selecionados passam para status **ativo**

---

### UC-04 — Acompanhar o dashboard
**Como** operador fiscal,
**quero** visualizar um painel consolidado das NF-e importadas e dos cadastros,
**para que** eu tenha visibilidade do volume processado e das pendências de autorização.

**Fluxo principal:**
1. Operador acessa a tela principal após login
2. Visualiza contadores de NF-e por período (dia/mês/ano)
3. Visualiza totais e pendências de emitentes, destinatários e tributações
4. Consulta as últimas NF-e importadas com status de validação

---

### UC-05 — Gerenciar usuários
**Como** administrador,
**quero** criar, editar e desativar usuários do sistema,
**para que** apenas pessoas autorizadas tenham acesso à plataforma.

**Fluxo principal:**
1. Administrador acessa a gestão de usuários
2. Cria novo usuário informando nome, e-mail, senha e perfil (Padrão ou Administrador)
3. O sistema força troca de senha no primeiro login do novo usuário
4. Administrador pode editar dados, alterar perfil ou desativar o usuário a qualquer momento

---

### UC-06 — Recuperar senha
**Como** usuário,
**quero** recuperar o acesso à minha conta caso esqueça a senha,
**para que** eu não precise acionar o administrador para cada situação de bloqueio.

**Fluxo principal:**
1. Usuário acessa "Esqueci minha senha" na tela de login
2. Informa o e-mail cadastrado
3. O sistema gera uma senha temporária (registrada no log do servidor — em produção, enviada por e-mail via SMTP)
4. Usuário faz login com a senha temporária e é redirecionado para troca obrigatória de senha
