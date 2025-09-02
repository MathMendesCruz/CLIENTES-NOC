import streamlit as st
import pandas as pd

st.set_page_config(page_title="Relatório de Clientes por Login", layout="wide")
st.title("Relatório de Clientes por Login para o NOC")

st.write(
    """
    Envie dois arquivos:
    - Um arquivo com logins (apenas coluna de login)
    - Um arquivo base com login, nome/razão social e WhatsApp dos clientes

    O sistema irá identificar os clientes presentes nos dois arquivos e exibir o nome e WhatsApp conforme o login.
    """
)

col1, col2 = st.columns(2)
with col1:
    file_logins = st.file_uploader("1️⃣ Arquivo dos clientes SLOT/PON", type=["xlsx", "xls", "csv"], key="logins")
with col2:
    file_base = st.file_uploader("2️⃣ Arquivo com Login + Filial)", type=["xlsx", "xls", "csv"], key="base")

def read_file(file):
    if file.name.endswith('.csv'):
        try:
            df = pd.read_csv(file, sep=';')
            if df.shape[1] == 1:
                file.seek(0)
                df = pd.read_csv(file, sep=',')
            return df
        except Exception:
            file.seek(0)
            return pd.read_csv(file)
    else:
        return pd.read_excel(file)

if file_logins and file_base:
    df_logins = read_file(file_logins)
    df_base = read_file(file_base)

    st.subheader("Selecione as colunas:")

    with st.form("column_select_form"):
        login_col_logins = st.selectbox("Coluna de login no arquivo de logins", df_logins.columns)
        login_col_base = st.selectbox("Coluna de login no arquivo base", df_base.columns)
        nome_col_base = st.selectbox("Coluna de nome/razão social", df_base.columns)
        whatsapp_col_base = st.selectbox("Coluna de WhatsApp", df_base.columns)
        submitted = st.form_submit_button("Gerar Relatório")

    if submitted:
        # Normaliza os logins para garantir o match correto
        logins_proc = df_logins[login_col_logins].astype(str).str.strip().str.lower().unique()
        df_base['__login_proc__'] = df_base[login_col_base].astype(str).str.strip().str.lower()

        # Faz o merge para buscar nome e whatsapp pelo login
        resultado_encontrados = df_base[df_base['__login_proc__'].isin(logins_proc)][
            [login_col_base, nome_col_base, whatsapp_col_base]
        ].rename(
            columns={
                login_col_base: "Login",
                nome_col_base: "Nome/Razão Social",
                whatsapp_col_base: "WhatsApp"
            }
        )

        # Identifica logins não encontrados
        logins_encontrados = set(resultado_encontrados["Login"].astype(str).str.strip().str.lower())
        logins_nao_encontrados = [login for login in logins_proc if login not in logins_encontrados]

        # DataFrame dos não encontrados
        resultado_nao_encontrados = pd.DataFrame({
            "Login": logins_nao_encontrados
        })

        st.success(f"Encontrados {len(resultado_encontrados)} clientes com login correspondente.")
        st.dataframe(resultado_encontrados, use_container_width=True)
        csv_encontrados = resultado_encontrados.to_csv(index=False, sep=';', encoding='utf-8')
        st.download_button(
            label="📥 Baixar resultado encontrados em CSV",
            data=csv_encontrados,
            file_name="clientes_encontrados.csv",
            mime="text/csv"
        )

        st.warning(f"{len(logins_nao_encontrados)} logins/clientes não encontrados:")
        st.dataframe(resultado_nao_encontrados, use_container_width=True)
        csv_nao_encontrados = resultado_nao_encontrados.to_csv(index=False, sep=';', encoding='utf-8')
        st.download_button(
            label="📥 Baixar resultado não encontrados em CSV",
            data=csv_nao_encontrados,
            file_name="clientes_nao_encontrados.csv",
            mime="text/csv"
        )
else:
    st.info("Envie os dois arquivos para começar.")

# --- Conteúdo do app.py abaixo ---

st.markdown("---")
st.header("Formatador de Contatos CSV para o Opa!Suite")

uploaded_file = st.file_uploader("Envie seu arquivo CSV", type=["csv"], key="csv_formatador")

if uploaded_file:
    try:
        # Tentar ler o CSV com separador correto
        try:
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
        except Exception:
            df = pd.read_csv(uploaded_file, sep=',')
        st.subheader("Colunas encontradas:")
        st.write(df.columns.tolist())

        # Permitir ao usuário selecionar as colunas de nome e WhatsApp
        st.info("Selecione as colunas de Nome/Razão Social e WhatsApp/Celular abaixo:")
        colunas = df.columns.tolist()
        col_nome = st.selectbox(
            "Coluna de Nome/Razão Social", 
            colunas, 
            index=next((i for i, col in enumerate(colunas) if any(x in col.lower() for x in ['razão', 'nome'])), 0),
            key="nome_formatador"
        )
        col_whatsapp = st.selectbox(
            "Coluna de WhatsApp/Celular", 
            colunas, 
            index=next((i for i, col in enumerate(colunas) if any(x in col.lower() for x in ['whatsapp', 'celular'])), 1 if len(colunas) > 1 else 0),
            key="whatsapp_formatador"
        )

        # Lista para novos contatos
        if "novos_contatos" not in st.session_state:
            st.session_state["novos_contatos"] = []

        st.subheader("Adicionar novo contato manualmente:")
        with st.form("adicionar_contato"):
            novo_nome = st.text_input("Nome do contato")
            novo_whatsapp = st.text_input("WhatsApp do contato")
            adicionar = st.form_submit_button("Adicionar contato")
        if adicionar and novo_nome and novo_whatsapp:
            st.session_state["novos_contatos"].append({"name": novo_nome, "whatsapp": novo_whatsapp})
            st.success(f"Contato '{novo_nome}' adicionado!")

        if col_nome and col_whatsapp:
            df_formatado = df[[col_nome, col_whatsapp]].copy()
            df_formatado.columns = ["name", "whatsapp"]

            # Adiciona os contatos fixos ao final
            contatos_fixos = [
                {"name": "Daniel", "whatsapp": "(11) 9479-81529"},
                {"name": "Mateus", "whatsapp": "(11) 99190-5547"},
                {"name": "Leonel", "whatsapp": "(11) 91302-7842"},
                {"name": "Matheus", "whatsapp": "(11) 94887-6252"},
            ]
            # Adiciona os contatos manuais
            contatos_adicionais = st.session_state["novos_contatos"]
            df_formatado = pd.concat([df_formatado, pd.DataFrame(contatos_fixos + contatos_adicionais)], ignore_index=True)

            st.success("Colunas selecionadas com sucesso!")
            st.subheader("Pré-visualização:")
            st.dataframe(df_formatado)

            # Botão de download ANTES do texto formatado
            csv = df_formatado.to_csv(index=False)
            st.download_button(
                label="📥 Baixar CSV formatado",
                data=csv.encode("utf-8"),
                file_name="contatos_formatado.csv",
                mime="text/csv"
            )

            st.subheader("Resultado Formatado (texto com vírgula):")
            resultado_texto = "\n".join(f"{row['name']}, {row['whatsapp']}" for _, row in df_formatado.iterrows())
            st.code(resultado_texto, language="text")
        else:
            st.error("Selecione as colunas corretamente.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo: {e}")
