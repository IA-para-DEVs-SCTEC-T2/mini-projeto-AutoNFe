# Estrutura do Projeto AutoNFe

## Visão Geral

Este documento descreve a organização de pastas e arquivos do projeto AutoNFe

## Estrutura de Diretórios

```
mini-projeto-autonfe/
├── src/                          # Todo o código da aplicação
│   ├── agents/                   # Agentes do sistema multi-agente
│   │   ├── __init__.py
│   │   ├── agent1_leitura.py     # Agente de leitura de XML
│   │   ├── agent2_cadastro.py    # Agente de cadastro
│   │   ├── agent3_validacao.py   # Agente de validação
│   │   └── orquestrador.py       # Coordenador dos agentes
│   ├── database/                 # Camada de dados
│   │   ├── __init__.py
│   │   ├── models.py             # Modelos SQLAlchemy
│   │   ├── repository.py         # Repositórios e queries
│   │   └── serializers.py        # Serialização para JSON
│   ├── web/                      # Camada web (Flask)
│   │   ├── __init__.py
│   │   ├── main.py               # Aplicação Flask principal
│   │   ├── auth.py               # Autenticação e autorização
│   │   └── security.py           # Segurança e validações
│   ├── utils/                    # Utilitários
│   │   └── __init__.py
│   ├── config/                   # Configurações
│   │   └── __init__.py
│   ├── static/                   # Arquivos estáticos
│   │   ├── css/                  # Folhas de estilo
│   │   │   ├── app.css
│   │   │   ├── auth.css
│   │   │   └── style.css
│   │   ├── js/                   # JavaScript
│   │   │   ├── app.js
│   │   │   └── auth.js
│   │   └── images/               # Imagens
│   ├── templates/                # Templates HTML (Jinja2)
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── esqueci_senha.html
│   │   └── trocar_senha.html
│   ├── data/                     # Dados e recursos
│   │   ├── schemas/              # Esquemas XSD
│   │   │   └── leiauteNFe_v4.00.xsd
│   │   ├── xml_samples/          # Amostras XML para teste
│   │   │   ├── NFe1.xml
│   │   │   ├── NFe2.xml
│   │   │   ├── NFe3.xml
│   │   │   └── NFe4.xml
│   │   └── database/             # Banco de dados
│   │       └── autonfe.db        # SQLite (criado automaticamente)
│   └── tests/                    # Testes automatizados
│       ├── __init__.py
│       ├── test_agentes.py       # Testes unitários e de integração
│       └── fixtures/             # Arquivos de teste
│           └── nfe_exemplo.xml
├── scripts/                      # Scripts auxiliares
├── .env.example                  # Template de variáveis de ambiente
├── .gitignore                    # Arquivos ignorados pelo Git
├── requirements.txt              # Dependências Python
├── main.py                       # Ponto de entrada principal
└── README.md                     # Documentação principal
```

## Módulos Principais

### src/agents/
Contém os três agentes especializados do sistema:
- **agent1_leitura.py**: Lê e extrai dados de arquivos XML de NF-e
- **agent2_cadastro.py**: Cadastra emitentes, destinatários e tributações
- **agent3_validacao.py**: Valida valores fiscais e totalizadores
- **orquestrador.py**: Coordena a execução dos três agentes

### src/database/
Camada de acesso a dados:
- **models.py**: Modelos SQLAlchemy (tabelas do banco); banco em `src/data/database/autonfe.db`
- **repository.py**: Funções de consulta e manipulação de dados
- **serializers.py**: Conversão de modelos para JSON

### src/web/
Aplicação web Flask:
- **main.py**: Rotas e endpoints da API REST; aponta `template_folder` e `static_folder` para `src/templates` e `src/static`
- **auth.py**: Sistema de autenticação e autorização
- **security.py**: Validações de segurança (OWASP Top 10)

### src/static/
Arquivos estáticos servidos pelo Flask:
- **css/**: Folhas de estilo (`app.css`, `auth.css`, `style.css`)
- **js/**: Scripts JavaScript (`app.js`, `auth.js`)
- **images/**: Imagens da interface

### src/templates/
Templates HTML Jinja2 renderizados pelo Flask.
Referenciam estáticos com os caminhos `/static/css/` e `/static/js/`.

### src/data/
Recursos e dados:
- **schemas/**: Esquema XSD para validação de XML (`leiauteNFe_v4.00.xsd`)
- **xml_samples/**: Exemplos de NF-e para importação manual
- **database/**: Banco de dados SQLite (`autonfe.db`, criado automaticamente)

### src/tests/
Testes automatizados com pytest:
- **test_agentes.py**: Testes unitários e de integração (45 testes)
- **fixtures/**: Arquivos de teste (XMLs de exemplo)

### src/config/
Módulo de configurações da aplicação.

## Como Executar

### Instalação
```bash
pip install -r requirements.txt
```

### Executar a aplicação
```bash
python main.py
```

### Executar testes
```bash
pytest src/tests/ -v
```

## Convenções

### Nomenclatura
- **Arquivos Python**: snake_case (ex: `agent1_leitura.py`)
- **Classes**: PascalCase (ex: `AgenteLeitorNFe`)
- **Funções**: snake_case (ex: `processar_arquivo`)
- **Constantes**: UPPER_CASE (ex: `MAX_ARQUIVOS_LOTE`)

### Imports
Todos os imports devem usar caminhos absolutos a partir de `src`:
```python
from src.agents.orquestrador import Orquestrador
from src.database.models import NotaFiscal
from src.web.auth import login_requerido
```

### Estrutura de Testes
- Testes devem estar em `src/tests/`
- Arquivos de teste devem começar com `test_`
- Fixtures devem estar em `src/tests/fixtures/`

## Benefícios da Estrutura

1. **Organização Clara**: Todo o código da aplicação centralizado em `src/`
2. **Separação por Responsabilidade**: agents, database, web, static, templates, data, tests
3. **Escalabilidade**: Fácil adicionar novos módulos e funcionalidades
4. **Manutenibilidade**: Código mais fácil de encontrar e modificar
5. **Padrões Python**: Segue convenções da comunidade Python/Flask
6. **Imports Limpos**: Imports absolutos facilitam refatoração
