
import re
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(
    page_title="Análise de Conversas do WhatsApp",
    page_icon="💬",
    layout="wide"
)


def ler_conversa(arquivo):
    conteudo = None

    for codificacao in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            conteudo = arquivo.getvalue().decode(codificacao)
            break
        except UnicodeDecodeError:
            continue

    if conteudo is None:
        raise ValueError("Não foi possível ler o arquivo TXT.")

    padrao = re.compile(
        r"^\[?"
        r"(\d{1,2}/\d{1,2}/\d{2,4}),?\s+"
        r"(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?)"
        r"\]?\s*(?:-\s*)?(.*)$",
        re.IGNORECASE
    )

    mensagens = []
    atual = None

    for linha in conteudo.splitlines():
        resultado = padrao.match(linha)

        if resultado:
            if atual is not None:
                mensagens.append(atual)

            data, hora, restante = resultado.groups()
            partes = re.split(r":\s", restante, maxsplit=1)

            if len(partes) == 2:
                remetente, mensagem = partes
            else:
                remetente = "Sistema"
                mensagem = restante

            atual = {
                "data": data,
                "hora": hora.strip(),
                "nome do remetente": remetente.strip(),
                "mensagem": mensagem
            }

        elif atual is not None:
            atual["mensagem"] += "\n" + linha

    if atual is not None:
        mensagens.append(atual)

    if not mensagens:
        raise ValueError("Nenhuma mensagem reconhecida no arquivo TXT.")

    df = pd.DataFrame(mensagens)

    df["data"] = pd.to_datetime(
        df["data"],
        dayfirst=False,
        errors="coerce"
    )

    df = df.dropna(subset=["data"]).copy()

    if df.empty:
        raise ValueError("Não foi possível interpretar as datas.")

    return df.reset_index(drop=True)


st.title("💬 Análise de Conversas do WhatsApp")
st.write(
    "Envie uma conversa exportada do WhatsApp em formato TXT "
    "para visualizar estatísticas e gráficos."
)

arquivo = st.file_uploader("Selecione o arquivo TXT", type=["txt"])

if arquivo is not None:
    try:
        df = ler_conversa(arquivo)

        st.success(
            f"Arquivo carregado! Foram encontrados {len(df)} registros."
        )

        # 1. Tabela completa
        st.subheader("1. Tabela completa de mensagens")
        st.dataframe(df, use_container_width=True)

        # 2. Resumo por remetente
        st.subheader("2. Quantidade de mensagens por remetente")

        resumo = (
            df["nome do remetente"]
            .value_counts()
            .rename_axis("Remetente")
            .reset_index(name="Quantidade de mensagens")
        )

        st.dataframe(resumo, use_container_width=True)

        remetentes = sorted(df["nome do remetente"].unique())

        # 3. Histórico do remetente
        st.subheader("3. Histórico do remetente")

        selecionado = st.selectbox(
            "Escolha o remetente",
            remetentes
        )

        df_selecionado = df[
            df["nome do remetente"] == selecionado
        ].copy()

        st.write(f"Mensagens de {selecionado}:")

        st.dataframe(
            df_selecionado[["data", "hora", "mensagem"]],
            use_container_width=True
        )

        # Gráfico diário do remetente
        st.subheader("4. Gráfico diário do remetente")

        por_dia = df_selecionado.groupby("data").size()

        fig1, ax1 = plt.subplots()
        por_dia.plot(kind="bar", ax=ax1)

        ax1.set_title(f"Mensagens por dia — {selecionado}")
        ax1.set_xlabel("Data")
        ax1.set_ylabel("Quantidade de mensagens")

        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        st.pyplot(fig1)
        plt.close(fig1)

        # 5. Gráfico de pizza
        st.subheader("5. Percentual de mensagens por remetente")

        contagem = df["nome do remetente"].value_counts()

        fig2, ax2 = plt.subplots()
        ax2.pie(
            contagem.values,
            labels=contagem.index,
            autopct="%1.1f%%",
            startangle=90
        )

        ax2.set_title("Participação de cada remetente")
        st.pyplot(fig2)
        plt.close(fig2)

        # 6. Gráfico de linhas
        st.subheader("6. Evolução diária das mensagens por remetente")

        diario = (
            df.groupby(["data", "nome do remetente"])
            .size()
            .unstack(fill_value=0)
            .sort_index()
        )

        fig3, ax3 = plt.subplots(figsize=(12, 5))

        for remetente in diario.columns:
            ax3.plot(
                diario.index,
                diario[remetente],
                marker="o",
                label=remetente
            )

        ax3.set_title("Mensagens por dia — todos os remetentes")
        ax3.set_xlabel("Data")
        ax3.set_ylabel("Quantidade de mensagens")
        ax3.legend(bbox_to_anchor=(1.02, 1), loc="upper left")

        fig3.autofmt_xdate()
        fig3.tight_layout()
        st.pyplot(fig3)
        plt.close(fig3)

    except Exception as erro:
        st.error(f"Erro ao processar o arquivo: {erro}")

else:
    st.info("Aguardando o envio de um arquivo TXT.")