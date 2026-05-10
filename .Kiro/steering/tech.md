# Infraestrutura Técnica — AutoNFe

## 1. Pilha de Tecnologia (Tech Stack)

### Backend
| Camada | Tecnologia | Papel |
|---|---|---|
| Runtime | Python | Linguagem principal da aplicação |
| Web Framework | Flask | API REST + templates Jinja2 para autenticação |
| ORM | SQLAlchemy | Mapeamento objeto-relacional e acesso ao banco |
| Banco de Dados | SQLite | Armazenamento local (`autonfe.db`) |
| Parser XML | lxml | Leitura e validação de NF-e com suporte a XSD |
| Segurança de senhas | Werkzeug (bcrypt) | Hash e verificação de senhas — já incluso no Flask |
| Cálculos financeiros | decimal (stdlib) | Precisão em operações monetárias — sem ponto flutuante |

### Frontend
| Camada | Tecnologia | Papel |
|---|---|---|
| Dashboard | Vanilla JS (SPA) | Interface principal sem framework externo |
| Autenticação | Jinja2 (templates) | Telas de login, troca de senha e recuperação |
| Estilo | CSS puro | Sem pré-processadores ou frameworks CSS |

### Ferramentas de Qualidade e Versionamento
| Ferramenta | Papel |
|---|---|
| pytest | Framework de testes unitários |
| pytest-cov | Relatório de cobertura de testes |
| Husky | Git hooks — executa commitlint antes de cada commit |
| commitlint | Valida mensagens de commit no padrão Conventional Commits |

---

## 2. Versões

| Tecnologia | Versão | Observação |
|---|---|---|
| Python | 3.11+ (testado em 3.14) | Mínimo 3.11; 3.14 requer versões específicas das libs |
| Flask | 3.0.3 | Fixado no requirements.txt |
| lxml | >= 6.1.0 | Mínimo 6.1.0 — wheel pré-compilado para Python 3.14 |
| SQLAlchemy | >= 2.0.36 | Mínimo 2.0.36 — corrige bug com `FastIntFlag` no Python 3.14 |
| Werkzeug | >= 3.0.0 | Dependência transitiva do Flask |
| pytest | 8.2.2 | Fixado no requirements.txt |
| pytest-cov | 5.0.0 | Fixado no requirements.txt |
| Node.js | >= 18 | Apenas para ferramentas de commit (commitlint + husky) |
| @commitlint/cli | ^20.5.2 | Validação de mensagens de commit |
| husky | ^9.1.7 | Git hooks |

> **Atenção:** `lxml==5.2.2` e `sqlalchemy==2.0.30` (versões originais) não são compatíveis com Python 3.14. Sempre usar as versões mínimas definidas acima.

---

## 3. Ferramentas e Infraestrutura

### Execução
- Servidor de desenvolvimento: `python main.py` — Flask built-in server em `127.0.0.1:5000`
- Banco criado automaticamente na primeira execução via `criar_tabelas()` + `seed_admin()`
- Sem Docker, sem serviços externos — tudo local por design

### Testes
```bash
# Execução simples
pytest tests/ -v

# Com cobertura
pytest tests/ -v --cov=agents --cov=database --cov-report=term-missing
```

### Git Hooks (Husky + commitlint)
- Configurado em `.husky/commit-msg`
- Valida automaticamente cada mensagem de commit contra o padrão Conventional Commits
- Configuração em `commitlint.config.cjs`

### Variáveis de Ambiente
| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | gerada aleatoriamente | Chave de sessão Flask — definir em produção |
| `NFE_API_TOKEN` | gerado aleatoriamente | Token de autenticação da API — definir em produção |
| `NFE_MAX_ARQUIVOS_LOTE` | `50` | Limite de arquivos por importação em lote |
| `FLASK_DEBUG` | `0` | Habilitar debug mode (`1` apenas em desenvolvimento) |
| `FLASK_HOST` | `127.0.0.1` | Host do servidor Flask |
| `FLASK_PORT` | `5000` | Porta do servidor Flask |

### Schema XSD
- Arquivo: `Apoio/leiauteNFe_v4.00.xsd`
- Usado pelo Agente 1 para validação estrutural opcional do XML da NF-e
- Validação ativada via `Orquestrador(db, validar_schema=True)`

---

## 4. Padrões de Código e Convenções

### Estilo Python
- `from __future__ import annotations` em todos os módulos Python
- Type hints em todas as assinaturas de funções e métodos
- Docstrings em classes e funções públicas
- Funções puras (sem efeitos colaterais) para parsing e cálculos — facilita testes
- Nomes em **português** para variáveis de domínio de negócio (emitente, destinatario, nota)
- Nomes em **inglês** para infraestrutura técnica (engine, session, logger)

### Padrões de Projeto Utilizados
| Padrão | Onde | Descrição |
|---|---|---|
| Pipeline / Chain | `Orquestrador` | Agente 1 → 2 → 3 em sequência coordenada |
| Repository | `database/repository.py` | Centraliza todas as queries, isolando o acesso a dados das rotas |
| Decorator | `auth.py`, `security.py` | `@login_requerido`, `@admin_requerido`, `@requer_autenticacao` |
| Dataclass | `agents/` | Estruturas de resultado imutáveis entre agentes |
| Context Manager | `database/repository.py` | `sessao_db()` garante fechamento de sessão |

### Convenções de Nomenclatura
| Elemento | Convenção | Exemplo |
|---|---|---|
| Classes | PascalCase | `AgenteLeitorNFe`, `ResultadoLeitura` |
| Funções e métodos | snake_case | `processar_bytes()`, `validar_senha_forte()` |
| Constantes | UPPER_SNAKE_CASE | `MAX_ARQUIVOS_LOTE`, `NFE_NAMESPACE` |
| Privados/internos | prefixo `_` | `_API_TOKEN`, `_parse_emitente()` |
| Tabelas do banco | snake_case plural | `notas_fiscais`, `itens_nota` |
| Rotas Flask | kebab-case | `/api/emitentes`, `/trocar-senha` |

### Mensagens de Commit (Conventional Commits)
```
feat: nova funcionalidade
fix: correção de bug
docs: alterações na documentação
refactor: refatoração sem alteração de comportamento
test: adição ou ajuste de testes
chore: tarefas de manutenção
```

---

## 5. Restrições Técnicas

### Obrigatório
- **Python puro** no backend — sem TypeScript, sem Node.js para lógica de negócio
- **`decimal.Decimal`** para todos os cálculos financeiros — nunca `float`
- **`datetime.now()`** para timestamps — sem UTC, horário local do servidor
- **Werkzeug `generate_password_hash` / `check_password_hash`** para senhas — nunca texto claro
- **`secrets.compare_digest()`** para comparação de tokens — evita timing attacks
- **`resolve_entities=False, no_network=True`** no parser lxml — proteção contra XXE
- **Sessões SQLAlchemy via context manager** (`sessao_db()`) — garante fechamento correto

### Proibido
- `float` para valores monetários ou fiscais
- Hardcode de `SECRET_KEY` ou `NFE_API_TOKEN` no código-fonte
- `debug=True` em produção
- Queries SQL raw sem ORM (usar SQLAlchemy)
- Armazenar senhas em texto claro
- Commitar `autonfe.db` no repositório (está no `.gitignore`)
- Bibliotecas externas para o frontend — apenas Vanilla JS

### Segurança (OWASP Top 10)
- Todas as rotas de API exigem header `X-API-Token`
- Telas de autenticação exigem sessão Flask ativa
- Headers HTTP de segurança aplicados globalmente: `CSP`, `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`, `Referrer-Policy`
- Nomes de arquivo sanitizados antes de qualquer uso (anti-XSS e path traversal)
- Limite de 50 arquivos por lote (anti-DoS) — configurável via `NFE_MAX_ARQUIVOS_LOTE`
- Logging de auditoria em todas as importações, autorizações e acessos negados
