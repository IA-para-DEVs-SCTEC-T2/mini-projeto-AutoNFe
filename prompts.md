# Histórico de Prompts

## Configuração Inicial do Projeto

### 1. Validação do Husky + Commitlint
> Configure o projeto para utilizarmos husky + commitlint na validação de commits semanticos do projeto.

---

## Documentação do Projeto

### 2. Redação do README
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

### 3. Seção "Como Usar"
> Adicione uma seção de como utilizar o app.
> ex: faça o clone, rode o comando x.

