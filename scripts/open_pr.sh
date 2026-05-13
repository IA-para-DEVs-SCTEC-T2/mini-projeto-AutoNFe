#!/bin/bash

set -e

BRANCH=$(git branch --show-current)

ISSUE_ID=$(echo "$BRANCH" | sed -E 's#^[a-zA-Z]+/([0-9]+)-.*$#\1#')

if [ -z "$ISSUE_ID" ] || [ "$ISSUE_ID" = "$BRANCH" ]; then
    echo "Erro: não foi possível identificar o número da Issue pela branch."
    echo "Use o padrão: feature/6-busca-produtos, docs/6-atualizar-readme ou fix/6-corrigir-bug"
    exit 1
fi

ISSUE_TITLE=$(gh issue view "$ISSUE_ID" --json title --jq '.title')

PR_TITLE=$(echo "$ISSUE_TITLE" \
  | sed -E 's/\[(STORY|EPIC|DOCS|TECH|BUG)\]//g' \
  | sed -E 's/^ *//g')

COMMIT_TYPE="feat"

if [[ "$BRANCH" == docs/* ]]; then
    COMMIT_TYPE="docs"
elif [[ "$BRANCH" == fix/* ]]; then
    COMMIT_TYPE="fix"
fi

BODY_FILE=$(mktemp)

cat > "$BODY_FILE" <<EOF
## O que foi feito

Implementação relacionada à Issue #$ISSUE_ID.

## Issue relacionada
Closes #$ISSUE_ID

## Validação da Issue
- [ ] Todos os itens aplicáveis do checklist técnico da Issue foram concluídos
- [ ] Os critérios BDD foram considerados, quando aplicável
- [ ] A Issue relacionada está pronta para ser fechada

## Checklist
- [ ] A User Story foi considerada, quando aplicável
- [ ] O código foi testado, quando aplicável
- [ ] A documentação foi atualizada, quando necessário
EOF

git push -u origin "$BRANCH"

gh pr create \
  --base main \
  --head "$BRANCH" \
  --title "$COMMIT_TYPE: $PR_TITLE" \
  --body-file "$BODY_FILE"

rm "$BODY_FILE"
