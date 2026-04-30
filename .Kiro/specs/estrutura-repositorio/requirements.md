# Documento de Requisitos

## Introdução

Este documento define os requisitos para a organização e padronização completa do repositório Git do projeto **AutoNFe**, seguindo o GitFlow definido na steering do projeto. O objetivo é garantir que o repositório possua estrutura de pastas clara, arquivos de configuração e governança adequados, automação de CI via GitHub Actions, e documentação de contribuição que permita a qualquer colaborador entender e seguir os padrões do projeto.

O projeto já possui: repositório Git local inicializado, branches `main`, `develop` e `feature/exemplo-gitflow`, tag `v1.0.0` em `main`, e steering de GitFlow em `.kiro/steering/gitflow.md`.

---

## Glossário

- **Repositório**: O repositório Git local e remoto do projeto AutoNFe.
- **GitFlow**: Modelo de branching definido em `.kiro/steering/gitflow.md`, com branches `main`, `develop`, `feature/*`, `fix/*`, `hotfix/*` e `release/*`.
- **CI**: Integração Contínua — pipeline automatizado que executa testes a cada Pull Request.
- **GitHub_Actions**: Plataforma de automação do GitHub que executa workflows definidos em `.github/workflows/`.
- **PR_Template**: Arquivo Markdown em `.github/PULL_REQUEST_TEMPLATE.md` que pré-preenche a descrição de Pull Requests.
- **Issue_Template**: Arquivos Markdown em `.github/ISSUE_TEMPLATE/` que estruturam a abertura de Issues.
- **CONTRIBUTING**: Arquivo `CONTRIBUTING.md` na raiz do repositório com guia de contribuição.
- **CHANGELOG**: Arquivo `CHANGELOG.md` na raiz do repositório que registra mudanças por versão seguindo o formato Keep a Changelog.
- **Badge**: Elemento visual no `README.md` que exibe status dinâmico (CI, versão, cobertura).
- **Proteção_de_Branch**: Conjunto de regras configuradas no GitHub que impedem commits diretos e exigem revisão em branches protegidas.
- **Pytest**: Framework de testes Python utilizado no projeto, configurado em `requirements.txt`.
- **Cobertura**: Percentual de linhas de código exercitadas pelos testes, medido pelo `pytest-cov`.
- **Conventional_Commits**: Padrão de mensagens de commit definido na steering: `<tipo>(<escopo>): <descrição>`.
- **SemVer**: Versionamento Semântico no formato `vMAJOR.MINOR.PATCH`.

---

## Requisitos

### Requisito 1: Estrutura de Pastas do Repositório

**User Story:** Como desenvolvedor do projeto, quero que o repositório tenha uma estrutura de pastas padronizada e documentada, para que qualquer colaborador entenda onde cada tipo de arquivo deve ser criado ou encontrado.

#### Critérios de Aceitação

1. THE Repositório SHALL conter as pastas `agents/`, `database/`, `static/`, `templates/`, `tests/`, `docs/` e `.kiro/` na raiz do projeto.
2. THE Repositório SHALL conter um arquivo `docs/PRD.md` com a documentação de produto do sistema.
3. THE Repositório SHALL conter um arquivo `Apoio/leiauteNFe_v4.00.xsd` com o schema XSD da NF-e v4.00.
4. THE README SHALL documentar a estrutura de pastas com descrição de cada diretório e seu propósito.
5. WHEN um novo arquivo de código Python é criado, THE Repositório SHALL posicioná-lo no diretório correspondente à sua responsabilidade (`agents/`, `database/` ou raiz para `app.py`).

---

### Requisito 2: Arquivo .gitignore Completo

**User Story:** Como desenvolvedor, quero um `.gitignore` completo e adequado ao projeto Python/Flask, para que arquivos gerados, segredos e artefatos de build nunca sejam versionados acidentalmente.

#### Critérios de Aceitação

1. THE Repositório SHALL conter um arquivo `.gitignore` na raiz com regras para ignorar arquivos gerados pelo Python (`__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`, `*.egg-info/`, `dist/`, `build/`).
2. THE Repositório SHALL conter regras no `.gitignore` para ignorar ambientes virtuais (`venv/`, `.venv/`, `env/`).
3. THE Repositório SHALL conter regras no `.gitignore` para ignorar arquivos de banco de dados local (`*.db`, `*.sqlite`, `*.sqlite3`).
4. THE Repositório SHALL conter regras no `.gitignore` para ignorar artefatos de cobertura de testes (`.coverage`, `htmlcov/`, `.pytest_cache/`).
5. THE Repositório SHALL conter regras no `.gitignore` para ignorar arquivos de IDEs (`.vscode/`, `.idea/`, `*.swp`, `*.swo`).
6. THE Repositório SHALL conter regras no `.gitignore` para ignorar arquivos de sistema operacional (`.DS_Store`, `Thumbs.db`).
7. THE Repositório SHALL conter regras no `.gitignore` para ignorar arquivos de log (`*.log`).
8. THE Repositório SHALL conter regras no `.gitignore` para ignorar arquivos de variáveis de ambiente (`.env`, `.env.local`, `.env.*.local`).
9. IF um arquivo listado no `.gitignore` for adicionado ao staging, THEN o Git SHALL ignorá-lo e não incluí-lo no commit.

---

### Requisito 3: Template de Pull Request

**User Story:** Como desenvolvedor, quero um template de Pull Request padronizado, para que toda PR aberta já contenha as seções obrigatórias definidas no GitFlow e reduza o esforço de preenchimento.

#### Critérios de Aceitação

1. THE Repositório SHALL conter o arquivo `.github/PULL_REQUEST_TEMPLATE.md`.
2. THE PR_Template SHALL conter a seção "O que foi feito" para descrição objetiva das mudanças.
3. THE PR_Template SHALL conter a seção "Como testar" com espaço para passo a passo de validação.
4. THE PR_Template SHALL conter a seção "Checklist" com os itens: testes passando (`pytest tests/ -v`), sem erros de diagnóstico, documentação atualizada se necessário, e branch atualizada com develop via rebase.
5. THE PR_Template SHALL conter a seção "Tipo de mudança" com opções: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`, `style`, `perf`.
6. WHEN um Pull Request é aberto no GitHub, THE GitHub SHALL pré-preencher a descrição com o conteúdo do PR_Template.

---

### Requisito 4: Templates de Issues

**User Story:** Como desenvolvedor ou usuário, quero templates de Issues padronizados, para que relatórios de bug e solicitações de feature contenham as informações necessárias para triagem e implementação.

#### Critérios de Aceitação

1. THE Repositório SHALL conter o arquivo `.github/ISSUE_TEMPLATE/bug_report.md` para relato de bugs.
2. THE Repositório SHALL conter o arquivo `.github/ISSUE_TEMPLATE/feature_request.md` para solicitação de novas funcionalidades.
3. THE Issue_Template de bug SHALL conter campos para: descrição do comportamento atual, comportamento esperado, passos para reproduzir, ambiente (SO, versão Python, versão do sistema) e logs relevantes.
4. THE Issue_Template de feature SHALL conter campos para: descrição da funcionalidade desejada, motivação e contexto, e critérios de aceitação sugeridos.
5. WHEN uma Issue é aberta no GitHub, THE GitHub SHALL apresentar a seleção entre os templates disponíveis.

---

### Requisito 5: Configuração de Proteção de Branches

**User Story:** Como mantenedor do projeto, quero que as regras de proteção de branches estejam documentadas, para que qualquer pessoa que configure o repositório remoto saiba exatamente quais proteções aplicar em `main` e `develop`.

#### Critérios de Aceitação

1. THE CONTRIBUTING SHALL documentar as regras de proteção para a branch `main`: commits diretos bloqueados, exigência de Pull Request, mínimo de 1 aprovação, e status check de CI obrigatório antes do merge.
2. THE CONTRIBUTING SHALL documentar as regras de proteção para a branch `develop`: commits diretos bloqueados, exigência de Pull Request, e status check de CI obrigatório antes do merge.
3. THE CONTRIBUTING SHALL documentar o passo a passo para configurar as proteções no GitHub em Settings → Branches → Branch protection rules.
4. THE CONTRIBUTING SHALL especificar que force push é proibido em `main` e `develop`.
5. THE CONTRIBUTING SHALL especificar que deleção das branches `main` e `develop` deve ser bloqueada.

---

### Requisito 6: GitHub Actions para CI

**User Story:** Como desenvolvedor, quero que os testes do projeto sejam executados automaticamente em todo Pull Request, para que regressões sejam detectadas antes do merge e a qualidade do código seja mantida.

#### Critérios de Aceitação

1. THE Repositório SHALL conter o arquivo `.github/workflows/ci.yml` com o workflow de CI.
2. WHEN um Pull Request é aberto ou atualizado com destino às branches `main` ou `develop`, THE GitHub_Actions SHALL executar o workflow de CI automaticamente.
3. WHEN o workflow de CI é executado, THE GitHub_Actions SHALL instalar as dependências listadas em `requirements.txt` usando `pip install -r requirements.txt`.
4. WHEN as dependências estão instaladas, THE GitHub_Actions SHALL executar `pytest tests/ -v --cov=agents --cov=database --cov-report=xml` para rodar os testes com cobertura.
5. IF algum teste falhar durante a execução do CI, THEN THE GitHub_Actions SHALL marcar o status check como falho e bloquear o merge do Pull Request.
6. WHEN todos os testes passam, THE GitHub_Actions SHALL marcar o status check como aprovado.
7. THE Workflow de CI SHALL executar em Python 3.11 para manter consistência com o ambiente de desenvolvimento.
8. THE Workflow de CI SHALL fazer upload do relatório de cobertura (`coverage.xml`) como artefato do workflow.
9. WHERE o repositório estiver configurado com Codecov, THE Workflow de CI SHALL enviar o relatório de cobertura para o Codecov após a execução dos testes.

---

### Requisito 7: Arquivo CONTRIBUTING.md

**User Story:** Como novo colaborador, quero um guia de contribuição completo, para que eu entenda como configurar o ambiente, seguir o GitFlow, escrever commits e abrir Pull Requests sem precisar consultar múltiplos documentos.

#### Critérios de Aceitação

1. THE Repositório SHALL conter o arquivo `CONTRIBUTING.md` na raiz do projeto.
2. THE CONTRIBUTING SHALL conter uma seção de pré-requisitos com as versões mínimas de Python (3.10+) e Git necessárias.
3. THE CONTRIBUTING SHALL conter uma seção de configuração do ambiente local com os comandos: clonar o repositório, criar ambiente virtual, instalar dependências com `pip install -r requirements.txt`, e executar os testes com `pytest tests/ -v`.
4. THE CONTRIBUTING SHALL conter uma seção descrevendo a estrutura de branches do GitFlow conforme definido na steering: `main`, `develop`, `feature/*`, `fix/*`, `hotfix/*`, `release/*`.
5. THE CONTRIBUTING SHALL conter uma seção com o fluxo completo para nova funcionalidade: criar branch a partir de `develop`, desenvolver com commits atômicos, manter branch atualizada via rebase, e abrir Pull Request.
6. THE CONTRIBUTING SHALL conter uma seção com o padrão de Conventional Commits em português, incluindo os tipos permitidos (`feat`, `fix`, `refactor`, `style`, `test`, `docs`, `chore`, `perf`) e exemplos.
7. THE CONTRIBUTING SHALL conter uma seção com as regras de Pull Request: título seguindo Conventional Commits, mínimo 1 aprovação, uso de Squash and Merge para features pequenas e Merge Commit para features grandes.
8. THE CONTRIBUTING SHALL conter uma seção com o fluxo de hotfix: criar a partir de `main`, corrigir, fazer merge em `main` com tag SemVer e merge em `develop`.
9. THE CONTRIBUTING SHALL conter uma seção de versionamento SemVer explicando os incrementos de MAJOR, MINOR e PATCH.

---

### Requisito 8: Arquivo CHANGELOG.md

**User Story:** Como desenvolvedor ou usuário, quero um CHANGELOG que registre todas as mudanças por versão, para que eu possa rastrear o histórico de evolução do sistema e entender o que mudou entre versões.

#### Critérios de Aceitação

1. THE Repositório SHALL conter o arquivo `CHANGELOG.md` na raiz do projeto.
2. THE CHANGELOG SHALL seguir o formato Keep a Changelog (https://keepachangelog.com/pt-BR/1.0.0/).
3. THE CHANGELOG SHALL conter a entrada para a versão `v1.0.0` com a data de lançamento e a lista de funcionalidades iniciais do sistema.
4. THE CHANGELOG SHALL organizar as mudanças por versão em ordem cronológica decrescente (versão mais recente no topo).
5. THE CHANGELOG SHALL utilizar as categorias: `Adicionado`, `Modificado`, `Corrigido`, `Removido` e `Segurança` para classificar as mudanças dentro de cada versão.
6. THE CHANGELOG SHALL conter uma seção `[Não Lançado]` no topo para registrar mudanças ainda não incluídas em uma versão oficial.
7. WHEN uma nova versão é lançada via branch `release/*`, THE CHANGELOG SHALL ser atualizado com a nova entrada de versão antes do merge em `main`.

---

### Requisito 9: Badges no README.md

**User Story:** Como desenvolvedor ou visitante do repositório, quero ver badges de status no README, para que eu possa verificar rapidamente o estado do CI, a versão atual e a cobertura de testes sem precisar navegar pelo repositório.

#### Critérios de Aceitação

1. THE README SHALL conter um badge de status do CI que exibe o resultado do último workflow executado na branch `main`.
2. THE README SHALL conter um badge de versão que exibe a tag SemVer mais recente do repositório (`v1.0.0`).
3. WHERE o repositório estiver configurado com Codecov, THE README SHALL conter um badge de cobertura de testes que exibe o percentual atual de cobertura.
4. THE README SHALL posicionar os badges no topo do arquivo, logo abaixo do título principal, antes de qualquer outra seção.
5. WHEN o workflow de CI é executado com sucesso, THE Badge de CI SHALL exibir o status "passing" (verde).
6. IF o workflow de CI falhar, THEN THE Badge de CI SHALL exibir o status "failing" (vermelho).
7. THE Badge de versão SHALL ser gerado a partir das tags do repositório usando o serviço `shields.io`.
