# Estrutura do Projeto AutoNFe

## Visão Geral

Este documento descreve a organização de pastas e arquivos do projeto AutoNFe

## Estrutura de Diretórios

```
autonfe/
├── src/                          # Código fonte principal
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
│   └── utils/                    # Utilitários
│       └── __init__.py
├── tests/                        # Testes automatizados
│   ├── __init__.py
│   ├── test_agentes.py           # Testes dos agentes
│   └── fixtures/                 # Arquivos de teste
│       └── nfe_exemplo.xml
├── config/                       # Configurações
│   └── __init__.py
├── static/                       # Arquivos estáticos
│   ├── css/                      # Folhas de estilo
│   │   ├── app.css
│   │   ├── auth.css
│   │   └── style.css
│   ├── js/                       # JavaScript
│   │   ├── app.js
│   │   └── auth.js
│   └── images/                   # Imagens
├── templates/                    # Templates HTML (Jinja2)
│   ├── index.html
│   ├── login.html
│   ├── esqueci_senha.html
│   └── trocar_senha.html
├── data/                         # Dados e recursos
│   ├── schemas/                  # Esquemas XSD
│   │   └── leiauteNFe_v4.00.xsd
│   ├── xml_samples/              # Amostras XML para teste
│   │   ├── NFe1.xml
│   │   ├── NFe2.xml
│   │   ├── NFe3.xml
│   │   └── NFe4.xml
│   └── database/                 # Banco de dados
│       └── autonfe.db            # SQLite (criado automaticamente)
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
- **models.py**: Modelos SQLAlchemy (tabelas do banco)
- **repository.py**: Funções de consulta e manipulação de dados
- **serializers.py**: Conversão de modelos para JSON

### src/web/
Aplicação web Flask:
- **main.py**: Rotas e endpoints da API REST
- **auth.py**: Sistema de autenticação e autorização
- **security.py**: Validações de segurança (OWASP Top 10)

### tests/
Testes automatizados com pytest:
- **test_agentes.py**: Testes unitários e de integração
- **fixtures/**: Arquivos de teste (XMLs de exemplo)

### data/
Recursos e dados:
- **schemas/**: Esquemas XSD para validação de XML
- **xml_samples/**: Exemplos de NF-e para importação
- **database/**: Banco de dados SQLite

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
pytest tests/ -v
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
- Testes devem estar em `tests/`
- Arquivos de teste devem começar com `test_`
- Fixtures devem estar em `tests/fixtures/`

## Benefícios da Estrutura

1. **Organização Clara**: Separação por responsabilidade (agents, database, web)
2. **Escalabilidade**: Fácil adicionar novos módulos e funcionalidades
3. **Manutenibilidade**: Código mais fácil de encontrar e modificar
4. **Padrões Python**: Segue convenções da comunidade Python/Flask
6. **Imports Limpos**: Imports absolutos facilitam refatoração
