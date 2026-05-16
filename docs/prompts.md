# Histórico de Prompts

## Configuração Inicial do Projeto

### 1. Validação do Husky + Commitlint
> Configure o projeto para utilizarmos husky + commitlint na validação de commits semanticos do projeto.

---

## Documentação do Projeto

### 2. Diagramas UML e C4 no PRD
> @renderMermaidDiagram utilizando contexto dos arquivos .Kiro\steering atualize o arquivo docs\PRD.md com 1 diagrama uml e 1 diagrama c4 (container).
> Atualize também na pasta docs\prompts.md o prompt que utilizarmos para essa construção

---

### 4. Redação do README
> Redija o README para as informações sobre o seguinte projeto.
>
> Criação de multiplos agentes para implantação de sistema com base em NF-e (XML) já emitados ou recebidos de fornecedores;
>
> 1 Agente de leitura de NF-e (XML) utilizar Esquemas XML "leiauteNFe_v4.00.xsd"
>     - Emitente e Destinatário
>     - Produto
>     - Tributação
>     - Leitura de valores e totalizadores
>
> 2 Agente Cadastro Emitente, Destinatário e Tributação
>     Recebe dados do Agente 1 e valida se os dados gravados existem no banco local
>     - Verificar se Emitente carregado pelo agente 1 se está cadastrado no banco de dados (local), se não tiver cadastrar, mas manter pendente para usuário autorizar
>     - Verificar se Destinatário carregado pelo agente 1 se está cadastrado no banco de dados (local), se não tiver cadastrar, mas manter pendente para usuário autorizar
>     - Verificar tributação carregado pelo agente 1 se está cadastrado no banco de dados (local), se não tiver cadastrar, mas manter pendente para usuário autorizar
>
> 3 Agente Validação de Valores
>     Recebe dados do Agente 1 valida valores
>     - Verificar se valores Base x Aliquota estão corretos
>     - Verificar se valores totalizados estão corretos conforme Itens
>
> 4 Dashboard
>     - Total de NF-e importadas com as opções dias, mes ou ano
>     - Total de Destinatário Cadastrada e pendente de autorização
>     - Total de Emitente Cadastrada e pendente de autorização
>     - Total de tributação Cadastrada e pendente de autorização
>
> 5 Autorização Cadastro
>     - Ao clicar na quantidade emitente, destinatário ou tributação, exibir tela com relação, usuário deve marcar o cadastro que deseja autorizar e confirmar.
>
> 6 Login
>     - Tela de login com autenticação por e-mail ou nome de usuário
>     - Senhas criptografadas com bcrypt (Werkzeug)
>     - Requisitos de senha: mínimo 8 caracteres, maiúscula, minúscula, número e caractere especial
>     - Primeiro login força troca de senha
>     - Recuperação de senha via senha temporária (simulada no log; configure SMTP para envio real)
>     - Troca de senha com validação da senha temporária
>     - Cadastro de usuários (somente administrador): Nome, E-mail, Senha, Tipo (Padrão/Administrador)
>     - Usuário administrador inicial: `admin@autonfe.local` ou `Administrador` / senha `sa` — troca de senha obrigatória no primeiro login
>     - Usuário de teste E2E: `test-autonfe` / senha `AutoNfe123#` — criado automaticamente, sem troca de senha obrigatória
>
> 7 Segurança
>     - Crie o projeto utilizando regras de segurança conforme `OWASP Pop 10` para evitar vulnerabilidades na aplicação

### 3. Seção "Como Usar"
> Adicione uma seção de como utilizar o app.
> ex: faça o clone, rode o comando x.

### 4. Configuração de gitActions
> Dentro da pasta .github/workflows crie um arquivo commitlint.yml com a configuração necessária para utilizarmos o gitHub Actions para análise de commits semânticos no PR

### Geral - criação de commits / PR´s
> adicione as alterações feitas, faça o commit baseado no padrão do projeto e abra um novo pr no repositório

---

## Testes E2E

### Testes automatizados com Playwright
> Utilizando Playwright, quero incluir um fluxo de teste E2E no sistema para validação do login. Em seguida, após a validação do login, quero que realize a importação de pelo menos uma nota no sistema, para validar a funcionalidade de importação de XML da NF-e.
>
> Contexto: A aplicação possui uma tela de login com os campos usuário ou e-mail, senha e botão para entrar. Após o login válido, o usuário deve ser direcionado para a tela de importação de XML.
>
> Cenário: O usuário acessa a tela de login, informa email e senha válidos, clica no botão Entrar e deve acessar a tela de importação de XML.
>
> Requisitos: Use pytest com Playwright em Python. Crie um nome claro para o teste. Use expect() do Playwright para validar URL e elementos da página. Gere comentários necessários dentro do teste.
>
> Gere o teste automatizado dentro da pasta src\tests\test-e2e

### Usuário de teste E2E
> Crie um usuário padrão para os testes E2E. Crie esse usuário já na inicialização da aplicação, junto com o banco.
>
> Usuário: test-autonfe
> Senha: AutoNfe123#
>
> E utilize esse usuário e senha como dados de entrada para realizar os testes que acabou de criar.

**Usuários criados automaticamente na inicialização da aplicação:**

| Perfil | Usuário / Login | Senha | Tipo | Troca de senha |
|--------|----------------|-------|------|----------------|
| Administrador | `admin@autonfe.local` | `sa` | administrador | Sim — obrigatória no primeiro login |
| Testes E2E | `test-autonfe` | `AutoNfe123#` | padrão | Não |

Ambos são gerados pelas funções `seed_admin()` e `seed_usuario_teste()` em `src/web/auth.py`, chamadas em `src/web/main.py` durante a inicialização.

**Comando para executar os testes E2E visualizando no navegador:**
```bash
pytest src/tests/test-e2e/test_login_e_importacao_nfe.py -v --headed --slowmo 800
```