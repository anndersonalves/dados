# 📊 Data Pilot

Painel de vendas em Python que também **conversa**: você pergunta em português e um agente de IA responde com as métricas que o código calculou.

> **Regra do projeto: o Python calcula, a IA só explica.** O modelo não inventa número. Ele escolhe qual função chamar, o Python executa, e o modelo só redige a resposta. Por isso dá para usar um modelo gratuito.

## O que o Data Pilot faz

A aplicação tem dois menus:

1. **Painel** — receita total, pedidos, ticket médio, clientes únicos, receita média por cliente, taxa de cancelamento, gráfico de receita por mês e as cinco cidades que mais vendem. Tudo filtrável por categoria.
2. **Conversa com os dados** — chat em que o modelo escolhe sozinho qual ferramenta chamar. Cada resposta traz um bloco "Como a resposta foi calculada" mostrando a função e os parâmetros usados.

### De onde vêm os dados

`data/sales.csv` é uma base **fictícia** de uma loja (1.225 linhas, jan–dez/2025), gerada com problemas propositais: datas em dois formatos, status escritos de vários jeitos, espaços sobrando e 25 pedidos duplicados. A limpeza produz `data/sales_clean.csv` (1.200 pedidos). Para usar a planilha real da loja, basta trocar o `sales.csv` (mesmas colunas) e rodar a limpeza de novo.

Colunas: `order_id`, `order_date`, `customer_id`, `city`, `category`, `product`, `quantity`, `unit_price`, `status`.

## Arquitetura em camadas

```
sales.csv ──► data_prep.py ──► metrics.py ──► app.py (painel)
 (cru)        (limpa)          (calcula)  └─► tools.py ──► chat.py ──► OpenRouter
                                              (descreve)    (executa pelo nome)
```

| Arquivo | Papel |
|---|---|
| `src/data_prep.py` | Converte datas, padroniza status, remove duplicados, cria `revenue`. Salva com `;` e vírgula decimal e lê do mesmo jeito. |
| `src/metrics.py` | Uma função por pergunta de negócio, sempre sobre pedidos **concluídos** (exceto a taxa de cancelamento, que olha todos os pedidos). |
| `src/tools.py` | Descreve cada função (nome, descrição, parâmetros) e executa a que o modelo pedir. |
| `src/chat.py` | Laço de chamada de ferramentas com o OpenRouter, sem framework de agentes. |
| `src/utils.py` | Formatação de R$ e milhares. |
| `app.py` | Interface Streamlit (painel + chat) com gráficos Plotly. |
| `tests/test_pipeline.py` | Testes da limpeza, das métricas, das ferramentas e do laço do chat. |

## Como instalar e rodar

Requer Python 3.10 ou superior.

```bash
# 1. Clone e entre na pasta
git clone https://github.com/SEU-USUARIO/data-pilot.git
cd data-pilot

# 2. Ambiente virtual e dependências
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure o .env (só necessário para o chat)
cp .env.example .env             # Windows: copy .env.example .env
# abra o .env e cole sua chave do OpenRouter (https://openrouter.ai/keys)

# 4. (Opcional) regenere o arquivo limpo
python -m src.data_prep

# 5. Rode o app — com streamlit, não com python
streamlit run app.py
```

O `.env` tem duas variáveis:

```
OPENROUTER_API_KEY=sua_chave
OPENROUTER_MODEL=openrouter/free
```

O `.env` está no `.gitignore`; só o `.env.example` é versionado. O painel funciona sem chave — só o chat precisa dela.

> O modelo gratuito tem limite de uso e velocidade variável, então uma resposta pode falhar de vez em quando. Se trocar de modelo, confira no OpenRouter se ele suporta **chamada de ferramentas**.

Para rodar os testes: `python -m pytest`

## Ferramentas que o modelo pode chamar

| Ferramenta | Responde |
|---|---|
| `obter_receita_total` | Quanto vendemos? |
| `obter_total_pedidos` | Quantos pedidos tivemos? |
| `obter_ticket_medio` | Quanto vale cada pedido, em média? |
| `obter_clientes_unicos` | Quantos clientes compraram? |
| `obter_taxa_cancelamento` | Qual % dos pedidos foi cancelada? |
| `obter_receita_media_por_cliente` | Quanto cada cliente gasta, em média? |
| `obter_receita_por_mes` | Como foram as vendas mês a mês? |
| `obter_top_cidades` | Quais cidades vendem mais? (parâmetro `quantidade`) |

Todas aceitam os parâmetros opcionais `categoria`, `data_inicio` e `data_fim` (formato `AAAA-MM-DD`).

Exemplos de perguntas:

- *Qual foi a receita total?*
- *Qual o ticket médio de Moda?*
- *Quais as 3 cidades que mais vendem?*
- *Qual a receita entre 2025-03-01 e 2025-05-31?*
- *Quanto cada cliente gasta em média?*

## Melhorias que escolhi

- **Métrica nova:** receita média por cliente (`receita_media_por_cliente`), no painel e no chat.
- **Gráfico novo:** as cinco cidades que mais vendem.
- **Intenção nova com parâmetro:** perguntas por período de datas (`data_inicio` / `data_fim`) e ranking com `quantidade` de cidades.
- **Portfólio:** este README, testes automatizados e o bloco "Como a resposta foi calculada" no chat, que mostra que o número vem do Python.

### Como a descrição da ferramenta influencia o modelo

O modelo escolhe a ferramenta lendo o nome e a **descrição**. `obter_ticket_medio` e `obter_receita_media_por_cliente` são parecidas, então cada descrição diz explicitamente que *não* é a outra ("por pedido" vs "por cliente"). Descrições vagas fazem o modelo errar a escolha; para testar, faça a mesma pergunta de formas diferentes e veja no bloco de cálculo qual função foi chamada.

## Conferência de consistência

Os números do chat e do painel vêm das **mesmas funções** de `src/metrics.py`. Com todas as categorias, o painel mostra:

| Métrica | Valor |
|---|---|
| Receita total | R$ 250.999,10 |
| Pedidos | 932 |
| Ticket médio | R$ 269,31 |
| Clientes únicos | 346 |
| Receita média por cliente | R$ 725,43 |
| Taxa de cancelamento | 15,33% |
