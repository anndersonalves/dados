"""Data Pilot — painel de vendas que também conversa.

Rode com:  streamlit run app.py   (não com `python app.py`)
"""
import plotly.express as px
import streamlit as st

from src import metrics
from src.chat import ErroDeConfiguracao, responder
from src.data_prep import carregar_vendas
from src.utils import brl, inteiro

st.set_page_config(page_title="Data Pilot", page_icon="📊", layout="wide")


@st.cache_data
def dados():
    return carregar_vendas()


df = dados()

st.sidebar.title("📊 Data Pilot")
menu = st.sidebar.radio("Menu", ["Painel", "Conversa com os dados"])
st.sidebar.caption("O Python calcula, a IA só explica.")


# ---------------------------------------------------------------- Painel
def pagina_painel():
    st.title("Painel de vendas")

    categorias = ["Todas"] + sorted(df["category"].unique().tolist())
    escolha = st.selectbox("Categoria", categorias)
    categoria = None if escolha == "Todas" else escolha

    c1, c2, c3 = st.columns(3)
    c1.metric("Receita total", brl(metrics.receita_total(df, categoria)))
    c2.metric("Pedidos", inteiro(metrics.total_pedidos(df, categoria)))
    c3.metric("Ticket médio", brl(metrics.ticket_medio(df, categoria)))

    c4, c5, c6 = st.columns(3)
    c4.metric("Clientes únicos", inteiro(metrics.clientes_unicos(df, categoria)))
    c5.metric(
        "Receita média por cliente", brl(metrics.receita_media_por_cliente(df, categoria))
    )
    c6.metric(
        "Taxa de cancelamento",
        f"{metrics.taxa_cancelamento(df, categoria):.2f}%".replace(".", ","),
    )

    st.subheader("Receita por mês")
    mensal = metrics.receita_por_mes(df, categoria)
    fig = px.bar(mensal, x="mes", y="receita", labels={"mes": "Mês", "receita": "Receita (R$)"})
    st.plotly_chart(fig, width="stretch")

    st.subheader("Cinco cidades que mais vendem")
    top = metrics.top_cidades(df, 5, categoria).sort_values("receita")
    fig2 = px.bar(
        top, x="receita", y="cidade", orientation="h",
        labels={"cidade": "Cidade", "receita": "Receita (R$)"},
    )
    st.plotly_chart(fig2, width="stretch")


# ---------------------------------------------------------------- Chat
def pagina_chat():
    st.title("Converse com os dados")
    st.caption(
        "Pergunte em português. O modelo escolhe uma função, o Python calcula e a IA explica. "
        "Ex.: *Qual o ticket médio de Moda?* · *Quais as 3 cidades que mais vendem?* · "
        "*Receita total entre 2025-03-01 e 2025-05-31*"
    )

    if "mensagens" not in st.session_state:
        st.session_state.mensagens = []  # {"role", "content", "ferramentas"}

    for m in st.session_state.mensagens:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("ferramentas"):
                with st.expander("Como a resposta foi calculada"):
                    for f in m["ferramentas"]:
                        st.code(f"{f['ferramenta']}({f['argumentos']})\n→ {f['resultado']}", language="text")

    pergunta = st.chat_input("Ex.: Qual foi a receita total?")
    if not pergunta:
        return

    with st.chat_message("user"):
        st.markdown(pergunta)

    historico = [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.mensagens
    ]
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                texto, usadas = responder(pergunta, historico, df)
            except ErroDeConfiguracao as e:
                texto, usadas = f"⚙️ {e}", []
            except Exception as e:
                texto, usadas = (
                    "Não consegui falar com o modelo agora. O modelo gratuito tem limite de uso "
                    f"e às vezes falha — tente de novo em instantes.\n\n`{type(e).__name__}: {e}`",
                    [],
                )
        st.markdown(texto)
        if usadas:
            with st.expander("Como a resposta foi calculada"):
                for f in usadas:
                    st.code(f"{f['ferramenta']}({f['argumentos']})\n→ {f['resultado']}", language="text")

    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    st.session_state.mensagens.append(
        {"role": "assistant", "content": texto, "ferramentas": usadas}
    )


if menu == "Painel":
    pagina_painel()
else:
    pagina_chat()
