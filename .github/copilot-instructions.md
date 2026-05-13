# Instruções do projeto para GitHub Copilot

Este repositório é uma demonstração de Engenharia de Software Assistida por IA usando GitHub,
GitHub Issues, GitHub Projects, branches, Pull Requests e documentação automatizada.

## Objetivo do projeto

O projeto simula o desenvolvimento do AutoNFe, um sistema de emissão e gerenciamento de
Notas Fiscais Eletrônicas (NF-e).

## Regras gerais

- Use linguagem técnica, objetiva e didática.
- Não invente funcionalidades que não existam no repositório.
- Ao gerar documentação, considere apenas arquivos existentes e comportamentos implementados.
- Ao gerar Issues, use Markdown com quebras reais.
- Nunca use `\n` escapado no corpo de Issues.
- Nunca use `--body $"texto\ntexto"` para criar Issues.
- Para Issues via terminal, use `--body-file` ou heredoc.
- Para `gh issue create`, não use `--json` nem `--jq`.
- Para capturar o número da Issue criada, capture a URL retornada pelo comando e extraia o número final com `sed`.

## Backlog

Use a seguinte estrutura:
- `[EPIC]` para agrupadores de alto nível.
- `[STORY]` para unidades principais de entrega.
- `[DOCS]` para documentação.

Tasks pequenas devem ficar como checklist técnico dentro da Story.
Critérios de aceitação devem ficar dentro da Story em BDD.

## Formato de Story

Cada Story deve conter:
- `Parent Epic: #ID`
- `## User Story`
- `## Critérios de aceitação — BDD`
- `## Checklist técnico`

## Fluxo de desenvolvimento

O fluxo padrão é:
1. Escolher uma Issue.
2. Rodar `./scripts/start_issue.sh`.
3. Implementar a alteração.
4. Fazer commit com Conventional Commits.
5. Rodar `./scripts/open_pr.sh`.
6. Revisar o Pull Request.
7. Fazer merge.
8. Apagar a branch após o merge.

## Convenção de branches

Use:
```text
feature/<issue-id>-descricao
fix/<issue-id>-descricao
docs/<issue-id>-descricao
refactor/<issue-id>-descricao
test/<issue-id>-descricao
chore/<issue-id>-descricao
```

## Convenção de commits

Use Conventional Commits:

```text
feat: implementa funcionalidade
fix: corrige comportamento
docs: atualiza documentação
chore: ajusta configuração
test: adiciona testes
refactor: refatora implementação
```

## Documentação

Ao atualizar `README.md` e `CONTRIBUTING.md`:
- Use Markdown organizado.
- Explique o objetivo do projeto.
- Explique a estrutura de pastas.
- Explique o fluxo com Issues, branches e Pull Requests.
- Explique como usar os scripts `start_issue.sh` e `open_pr.sh`.
- Não documente funcionalidades inexistentes.
