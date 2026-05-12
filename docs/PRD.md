# PRD — AutoNFe

## Diagramas de Arquitetura

---

### Diagrama UML de Classes

Representa as principais classes do sistema, seus atributos, métodos e relacionamentos.
Contexto: `.Kiro/steering/structure.md`, `.Kiro/steering/product.md`, `.Kiro/steering/tech.md`.

```mermaid
classDiagram
    class Orquestrador {
        -db: Session
        -validar_schema: bool
        +processar_nfe(arquivo_xml)
        +coordenar_agentes()
    }
    class AgenteLeitorNFe {
        +ler_xml(caminho: str)
        +validar_schema_xsd() bool
        +extrair_emitente() dict
        +extrair_destinatario() dict
        +extrair_produtos() list
        +extrair_tributacao() dict
        +extrair_totalizadores() dict
    }
    class AgenteCadastro {
        +cadastrar_emitente(dados: dict)
        +cadastrar_destinatario(dados: dict)
        +cadastrar_tributacao(dados: dict)
        +verificar_existencia(entidade: str) bool
    }
    class AgenteValidacao {
        +validar_valores(dados: dict) bool
        +verificar_base_aliquota() bool
        +verificar_totalizadores() bool
    }
    note for AgenteValidacao "Usa decimal (stdlib)\npara precisão monetária"
    class NotaFiscal {
        +id: int
        +chave_acesso: str
        +data_emissao: datetime
        +status: str
        +emitente_id: int
        +destinatario_id: int
    }
    class Emitente {
        +id: int
        +cnpj: str
        +razao_social: str
        +autorizado: bool
    }
    class Destinatario {
        +id: int
        +cnpj_cpf: str
        +razao_social: str
        +autorizado: bool
    }
    class Tributacao {
        +id: int
        +cst: str
        +aliquota: float
        +autorizado: bool
    }
    class Usuario {
        +id: int
        +nome: str
        +email: str
        +senha_hash: str
        +perfil: str
        +primeiro_login: bool
        +ativo: bool
    }
    class AuditLog {
        +id: int
        +acao: str
        +usuario_id: int
        +detalhes: str
        +timestamp: datetime
    }
    class FlaskApp {
        +template_folder: str
        +static_folder: str
        +processar_xml_route()
        +importar_lote_route()
        +dashboard_route()
        +autorizar_cadastro_route()
        +gerenciar_usuarios_route()
    }
    class Auth {
        +login_requerido()
        +autenticar_usuario(email, senha) bool
        +validar_token_api(token: str) bool
        +recuperar_senha(email)
        +forcar_troca_senha()
    }
    class Security {
        +validar_senha(senha) bool
        +criptografar_bcrypt(senha) str
        +verificar_bcrypt(senha, hash) bool
        +sanitizar_nome_arquivo(nome) str
        +proteger_xxe(parser) XMLParser
    }
    class Repository {
        +buscar_por_id(id) Model
        +salvar(entidade) Model
        +listar_pendentes() list
        +autorizar(id) bool
    }

    Orquestrador --> AgenteLeitorNFe : coordena
    Orquestrador --> AgenteCadastro : coordena
    Orquestrador --> AgenteValidacao : coordena
    AgenteLeitorNFe ..> NotaFiscal : extrai dados para
    AgenteCadastro --> Emitente : gerencia
    AgenteCadastro --> Destinatario : gerencia
    AgenteCadastro --> Tributacao : gerencia
    AgenteValidacao ..> NotaFiscal : valida
    FlaskApp --> Auth : usa
    FlaskApp --> Security : usa
    FlaskApp --> Orquestrador : dispara
    AgenteCadastro --> Repository : persiste via
    FlaskApp --> Repository : consulta via
    NotaFiscal --> Emitente : referencia
    NotaFiscal --> Destinatario : referencia
    FlaskApp --> AuditLog : registra eventos em
    Auth --> Usuario : autentica
    Auth --> AuditLog : registra acessos negados
    Repository --> Usuario : gerencia
    AuditLog --> Usuario : pertence a
```

---

### Diagrama C4 — Nível 2 (Containers)

Representa os containers do sistema AutoNFe, seus relacionamentos internos e dependências externas.
Contexto: `.Kiro/steering/structure.md`, `.Kiro/steering/product.md`, `.Kiro/steering/tech.md`.

```mermaid
C4Container
    title AutoNFe - Diagrama C4 Nível 2 (Containers)

    Person(usuario, "Usuário Operador", "Importa NF-e (individual ou lote até 50 arquivos), acompanha dashboard e autoriza cadastros")
    Person(admin, "Administrador", "Gerencia usuários, perfis e permissões do sistema")

    System_Boundary(autonfe, "Sistema AutoNFe") {
        Container(web_app, "Aplicação Web", "Python 3.11+ / Flask 3.0.3", "Rotas REST e templates Jinja2: dashboard, upload NF-e, importação em lote, autorização de cadastros e gestão de usuários")
        Container(orquestrador, "Orquestrador de Agentes", "Python", "Recebe db e flag validar_schema; coordena sequencialmente os três agentes especializados")
        Container(agent1, "Agente 1 - Leitura", "Python / lxml >= 6.1.0", "Lê XML da NF-e; validação estrutural opcional via XSD v4.00; extrai emitente, destinatário, produtos, tributação e totalizadores")
        Container(agent2, "Agente 2 - Cadastro", "Python / SQLAlchemy >= 2.0.36", "Verifica e cadastra emitentes, destinatários e tributações com status pendente aguardando aprovação")
        Container(agent3, "Agente 3 - Validação", "Python / decimal (stdlib)", "Valida Base × Alíquota (ICMS, IPI, PIS, COFINS) e confere totalizadores usando aritmética decimal")
        ContainerDb(db, "Banco de Dados", "SQLite / SQLAlchemy", "Tabelas: NotaFiscal, Emitente, Destinatario, Tributacao, Usuario, AuditLog — arquivo autonfe.db criado automaticamente")
        Container(static, "Front-end Estático", "Vanilla JS / CSS puro / Jinja2", "Dashboard SPA + telas de autenticação; assets em /static/css e /static/js")
        Container(env, "Configuração", ".env / Variáveis de Ambiente", "SECRET_KEY, NFE_API_TOKEN, NFE_MAX_ARQUIVOS_LOTE (50), FLASK_HOST:PORT, FLASK_DEBUG")
    }

    System_Ext(xml_nfe, "Arquivos XML NF-e", "NF-e v4.00 no padrão SEFAZ; validadas contra leiauteNFe_v4.00.xsd")
    System_Ext(smtp, "Servidor SMTP", "Envio de senha temporária para recuperação de acesso (opcional — simulado em log por padrão)")

    Rel(usuario, web_app, "Upload de XML, dashboard, autorização de cadastros", "HTTPS")
    Rel(admin, web_app, "Gestão de usuários e perfis", "HTTPS")
    Rel(web_app, static, "Serve templates e assets estáticos", "HTTP")
    Rel(web_app, env, "Lê configurações na inicialização")
    Rel(web_app, orquestrador, "Dispara pipeline de processamento de NF-e")
    Rel(orquestrador, agent1, "Delega leitura e validação do XML")
    Rel(orquestrador, agent2, "Delega cadastro de emitentes, destinatários e tributações")
    Rel(orquestrador, agent3, "Delega validação matemática dos valores")
    Rel(agent1, xml_nfe, "Lê e valida estrutura via XSD (opcional)")
    Rel(agent2, db, "Cria registros pendentes", "SQLAlchemy ORM")
    Rel(agent3, db, "Lê NF-e e itens para validação", "SQLAlchemy ORM")
    Rel(web_app, db, "Lê/Escreve NotaFiscal, Usuario, AuditLog", "SQLAlchemy ORM")
    Rel(web_app, smtp, "Envia senha temporária", "SMTP (opcional)")
```
