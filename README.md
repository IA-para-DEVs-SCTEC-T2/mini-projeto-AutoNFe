# AutoNFe — Sistema Multi-Agente para Processamento de NF-e

> Mini projeto — Curso IA para Devs

Sistema baseado em múltiplos agentes de inteligência artificial para automação da importação, validação e cadastro de dados provenientes de Notas Fiscais Eletrônicas (NF-e) em formato XML.

---

## Visão Geral

O **AutoNFe** processa arquivos XML de NF-e já emitidas ou recebidas de fornecedores, distribuindo as responsabilidades entre agentes especializados que trabalham de forma coordenada. O objetivo é reduzir o esforço manual de digitação, minimizar erros de cadastro e garantir a integridade dos valores fiscais importados.

---

## Arquitetura de Agentes

### Agente 1 — Leitura de NF-e (XML)

Responsável pela leitura e extração estruturada dos dados do XML, com base no esquema oficial **`leiauteNFe_v4.00.xsd`**.

Dados extraídos:

| Grupo | Campos |
|---|---|
| **Emitente** | CNPJ, Razão Social, Endereço, IE |
| **Destinatário** | CNPJ/CPF, Razão Social, Endereço, IE |
| **Produtos** | Código, Descrição, NCM, CFOP, Unidade, Quantidade, Valor Unitário |
| **Tributação** | ICMS, IPI, PIS, COFINS — bases, alíquotas e valores |
| **Totalizadores** | Valor dos produtos, frete, seguro, desconto, total da NF-e |

---

### Agente 2 — Cadastro de Emitente, Destinatário e Tributação

Recebe os dados extraídos pelo **Agente 1** e realiza a verificação e o cadastro no banco de dados local.

Fluxo para cada entidade:

```
Dados recebidos do Agente 1
        │
        ▼
Consulta no banco local ──── Encontrado ──▶ Nenhuma ação necessária
        │
     Não encontrado
        │
        ▼
Cadastra automaticamente com status: PENDENTE
        │
        ▼
Aguarda autorização do usuário (ver item 5)
```

Entidades gerenciadas:

- **Emitente** — verifica por CNPJ; cadastra se não existir (status: pendente)
- **Destinatário** — verifica por CNPJ/CPF; cadastra se não existir (status: pendente)
- **Tributação** — verifica combinação de CFOP + CST/CSOSN + alíquotas; cadastra se não existir (status: pendente)

---

### Agente 3 — Validação de Valores

Recebe os dados do **Agente 1** e realiza conferência matemática dos valores fiscais da NF-e.

Validações realizadas:

- **Base × Alíquota** — recalcula o valor de cada tributo (ICMS, IPI, PIS, COFINS) e compara com o valor declarado no XML
- **Totalizadores** — verifica se os valores totais da NF-e correspondem à soma dos itens, acrescido de frete, seguro e descontos
- Emite alertas para divergências encontradas

---

## Dashboard

Painel de controle com visão consolidada das NF-e importadas e do status dos cadastros.

| Indicador | Filtros disponíveis |
|---|---|
| Total de NF-e importadas | Dia / Mês / Ano |
| Emitentes cadastrados | Total / Pendentes de autorização |
| Destinatários cadastrados | Total / Pendentes de autorização |
| Tributações cadastradas | Total / Pendentes de autorização |

---

## Autorização de Cadastros

Fluxo de aprovação dos registros criados automaticamente pelo **Agente 2**:

1. No Dashboard, clique no contador de **Emitentes**, **Destinatários** ou **Tributações** pendentes
2. Uma tela exibirá a relação de registros com status **PENDENTE**
3. Selecione um ou mais registros para autorizar
4. Confirme — os registros selecionados passam para o status **ATIVO**

---

## Autenticação e Usuários
- Tela de login com autenticação por e-mail ou nome de usuário
- Senhas criptografadas com bcrypt (Werkzeug)
- Requisitos de senha: mínimo 8 caracteres, maiúscula, minúscula, número e caractere especial
- Primeiro login força troca de senha
- Recuperação de senha via senha temporária (simulada no log; configure SMTP para envio real)
- Troca de senha com validação da senha temporária
- Cadastro de usuários (somente administrador): Nome, E-mail, Senha, Tipo (Padrão/Administrador)
- Usuário administrador inicial: `admin@autonfe.local` / senha `sa`
- Controle de acesso por sessão Flask + token de API

---

## Segurança (OWASP Top 10)
- Autenticação obrigatória em todas as rotas (sessão + token API)
- Senhas com hash bcrypt — nunca armazenadas em texto claro
- Parser XML com `resolve_entities=False, no_network=True` (anti-XXE)
- Headers HTTP: CSP, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
- Sanitização de nomes de arquivo (anti-XSS e path traversal)
- Limite de 50 arquivos por lote (anti-DoS)
- `debug=False` por padrão; `SECRET_KEY` via variável de ambiente
- Logging de auditoria: importações, autorizações e acessos negados

---

## Tecnologias

- **Python 3.11+** — runtime principal
- **lxml** — leitura e validação de XML com suporte a XSD
- **SQLite** — banco de dados local
- **XML Schema (XSD)** — `leiauteNFe_v4.00.xsd` para validação e leitura estruturada do XML
- **Flask** — leve, adequado para APIs REST + servir o frontend e templates Jinja2
- **Werkzeug bcrypt** — hash de senhas seguro, já incluído no Flask
- **Decimal** — todos os cálculos financeiros usam `Decimal` para evitar erros de ponto flutuante
- **datetime.now()** — horário local do servidor (sem UTC) para exibição correta das datas
- **SPA + templates** — dashboard como SPA vanilla JS; telas de auth como templates Jinja2 tradicionais

---

## Como Usar

### Pré-requisitos

- Python 3.11 ou superior instalado
- `pip` disponível no PATH

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/mini-projeto-AutoNFe.git
cd mini-projeto-AutoNFe

# 2. Crie e ative o ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt
```

### Executando os Agentes

```bash
# Iniciar o pipeline completo (Agente 1 → 2 → 3)
python main.py
```

Acesse: **http://127.0.0.1:5000**

### Primeiro acesso

| Campo | Valor |
|-------|-------|
| Usuário | `admin@autonfe.local` |
| Senha | `sa` |

O sistema solicitará a troca de senha no primeiro login.

### Testes

```bash
# Todos os testes
pytest tests/ -v

# Com relatório de cobertura
pytest tests/ -v --cov=agents --cov=database --cov-report=term-missing
```

### Banco de Dados

Na primeira execução, o banco de dados local (`autonfe.db`) é criado automaticamente no diretório raiz do projeto.

---

## Padrão de Commits

Este projeto adota o padrão [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: nova funcionalidade
fix: correção de bug
docs: alterações na documentação
refactor: refatoração sem alteração de comportamento
test: adição ou ajuste de testes
chore: tarefas de manutenção
```
