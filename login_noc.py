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

# --- Upload dos arquivos principais ---
col1, col2 = st.columns(2)
with col1:
    file_logins = st.file_uploader("1️⃣ Arquivo dos clientes SLOT/PON", type=["xlsx", "xls", "csv"], key="logins")
with col2:
    file_base = st.file_uploader("2️⃣ Arquivo com Login + Filial", type=["xlsx", "xls", "csv"], key="base")

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
        login_col_logins = st.selectbox("Coluna de LOGIN no arquivo dos clientes SLOT/PON", df_logins.columns)
        nome_col_logins = st.selectbox("Coluna de NOME/RAZÃO SOCIAL no arquivo dos clientes SLOT/PON (opcional)", ["Nenhum"] + list(df_logins.columns))
        login_col_base = st.selectbox("Coluna de LOGIN no arquivo LOGIN_FILIAL", df_base.columns)
        nome_col_base = st.selectbox("Coluna de NOME/RAZÃO SOCIAL no arquivo LOGIN_FILIAL", df_base.columns)
        whatsapp_col_base = st.selectbox("Coluna de WHATSAPP no arquivo LOGIN_FILIAL", df_base.columns)
        submitted = st.form_submit_button("Gerar Relatório")

    if submitted:
        # --- Normalização e busca ---
        logins_raw = df_logins[login_col_logins].astype(str).str.strip().str.lower()
        nomes_raw = logins_raw.str.replace("_", " ")

        if nome_col_logins != "Nenhum" and nome_col_logins != login_col_logins:
            nomes_col = df_logins[nome_col_logins].astype(str).str.strip().str.lower()
            nomes_col_spaces = nomes_col.str.replace("_", " ")
            busca_proc = pd.concat([logins_raw, nomes_raw, nomes_col, nomes_col_spaces], ignore_index=True)
        else:
            busca_proc = pd.concat([logins_raw, nomes_raw], ignore_index=True)

        busca_proc = busca_proc[busca_proc != ""].drop_duplicates()
        busca_proc = busca_proc.str.strip().str.lower().drop_duplicates()

        base_login = df_base[login_col_base].astype(str).str.strip().str.lower()
        base_login_space = base_login.str.replace("_", " ")
        base_nome = df_base[nome_col_base].astype(str).str.strip().str.lower()
        base_nome_underscore = base_nome.str.replace(" ", "_")

        base_variacoes = pd.concat([base_login, base_login_space, base_nome, base_nome_underscore], ignore_index=True).drop_duplicates()

        encontrados = busca_proc[busca_proc.isin(base_variacoes)]
        nao_encontrados = busca_proc[~busca_proc.isin(base_variacoes)]

        mask_encontrados = (
            base_login.isin(encontrados) |
            base_login_space.isin(encontrados) |
            base_nome.isin(encontrados) |
            base_nome_underscore.isin(encontrados)
        )
        resultado_encontrados = df_base[mask_encontrados][[login_col_base, nome_col_base, whatsapp_col_base]].rename(
            columns={
                login_col_base: "Login",
                nome_col_base: "Nome/Razão Social",
                whatsapp_col_base: "WhatsApp"
            }
        ).drop_duplicates()

        resultado_nao_encontrados = pd.DataFrame({"Login ou Nome": nao_encontrados})

        # --- Inicializa estados se não existirem ---
        if "clientes_utilizados" not in st.session_state:
            st.session_state["clientes_utilizados"] = set()
        if "utilizados_importados_sucesso" not in st.session_state:
            st.session_state["utilizados_importados_sucesso"] = None

        # --- Criação das abas ---
        tab1, tab2, tab3, tab4 = st.tabs([
            "Encontrados", 
            "Não encontrados", 
            "Clientes já utilizados",
            "Importar utilizados"
        ])

        # --- Aba 1: Encontrados ---
        with tab1:
            encontrados_filtrados = resultado_encontrados[
                ~resultado_encontrados["Login"].str.lower().isin(st.session_state["clientes_utilizados"])
            ]
            st.success(f"Encontrados {len(encontrados_filtrados)} clientes do arquivo 1 na base.")
            st.dataframe(encontrados_filtrados, use_container_width=True)
            csv_encontrados = encontrados_filtrados.to_csv(index=False, sep=';', encoding='utf-8')
            st.download_button(
                label="📥 Baixar resultado encontrados em CSV",
                data=csv_encontrados,
                file_name="clientes_encontrados.csv",
                mime="text/csv"
            )

            selecionados = st.multiselect(
                "Marcar clientes como utilizados (serão excluídos das listas):",
                encontrados_filtrados["Login"].tolist(),
                key="multiselect_encontrados"
            )
            if st.button("Adicionar à lista de utilizados (aba Encont.)"):
                st.session_state["clientes_utilizados"].update([s.lower() for s in selecionados])
                st.success(f"{len(selecionados)} clientes adicionados à lista de utilizados!")

        # --- Aba 2: Não encontrados ---
        with tab2:
            nao_encontrados_filtrados = resultado_nao_encontrados[
                ~resultado_nao_encontrados["Login ou Nome"].str.lower().isin(st.session_state["clientes_utilizados"])
            ]
            st.warning(f"{len(nao_encontrados_filtrados)} logins/nome do arquivo 1 não encontrados na base:")
            st.dataframe(nao_encontrados_filtrados, use_container_width=True)
            csv_nao_encontrados = nao_encontrados_filtrados.to_csv(index=False, sep=';', encoding='utf-8')
            st.download_button(
                label="📥 Baixar resultado não encontrados em CSV",
                data=csv_nao_encontrados,
                file_name="clientes_nao_encontrados.csv",
                mime="text/csv"
            )

            selecionados_nao = st.multiselect(
                "Marcar clientes como utilizados (serão excluídos das listas):",
                nao_encontrados_filtrados["Login ou Nome"].tolist(),
                key="multiselect_nao_encontrados"
            )
            if st.button("Adicionar à lista de utilizados (aba Não Encont.)"):
                st.session_state["clientes_utilizados"].update([s.lower() for s in selecionados_nao])
                st.success(f"{len(selecionados_nao)} clientes adicionados à lista de utilizados!")

        # --- Aba 3: Clientes já utilizados ---
        with tab3:
            st.info("Clientes já utilizados (não aparecem nas listas acima):")
            st.write(list(st.session_state["clientes_utilizados"]))
            if st.button("Limpar lista de utilizados"):
                st.session_state["clientes_utilizados"] = set()
                st.success("Lista de clientes utilizados limpa!")

            st.markdown("---")
            st.subheader("Adicionar manualmente clientes utilizados")
            clientes_digitados = st.text_input(
                "Digite logins ou nomes separados por vírgula",
                key="input_utilizados_manual"
            )
            if st.button("Adicionar clientes digitados"):
                novos = [c.strip().lower() for c in clientes_digitados.split(",") if c.strip()]
                st.session_state["clientes_utilizados"].update(novos)
                st.success(f"{len(novos)} clientes adicionados manualmente à lista de utilizados!")

        # --- Aba 4: Importar clientes utilizados ---
        with tab4:
            st.info("Importe um arquivo CSV ou XLSX com as colunas login, nome/razão social e whatsapp para adicionar à lista de utilizados.")
            file_utilizados = st.file_uploader(
                "Arquivo de clientes já utilizados", 
                type=["csv", "xlsx", "xls"], 
                key="importar_utilizados_aba4"  # chave única!
            )

            if file_utilizados:
                try:
                    if file_utilizados.name.endswith(".csv"):
                        df_utilizados = pd.read_csv(file_utilizados)
                    else:
                        df_utilizados = pd.read_excel(file_utilizados)
                    
                    df_utilizados.columns = [col.lower().strip() for col in df_utilizados.columns]
                    col_login = next((col for col in df_utilizados.columns if "login" in col), None)
                    col_nome = next((col for col in df_utilizados.columns if "nome" in col or "razão" in col), None)

                    if col_login or col_nome:
                        utilizados_set = set()
                        if col_login:
                            utilizados_set.update(df_utilizados[col_login].astype(str).str.strip().str.lower())
                        if col_nome:
                            utilizados_set.update(df_utilizados[col_nome].astype(str).str.strip().str.lower())
                        utilizados_set = {u for u in utilizados_set if u}
                        st.session_state["clientes_utilizados"].update(utilizados_set)
                        st.success(f"{len(utilizados_set)} clientes adicionados à lista de utilizados!")
                    else:
                        st.error("Arquivo não possui coluna de login ou nome/razão social.")
                except Exception as e:
                    st.error(f"Erro ao processar o arquivo: {e}")
else:
    st.info("Envie os dois arquivos para começar.")

# --- Formatação de contatos CSV/Opa!Suite ---
st.markdown("---")
st.header("Formatador de Contatos CSV para o Opa!Suite")

uploaded_file = st.file_uploader("Envie seu arquivo CSV", type=["csv"], key="csv_formatador")

if uploaded_file:
    try:
        # Ler CSV
        try:
            df = pd.read_csv(uploaded_file, sep=None, engine='python')
        except Exception:
            df = pd.read_csv(uploaded_file, sep=',')

        st.subheader("Colunas encontradas:")
        st.write(df.columns.tolist())

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

            # Contatos fixos
            contatos_fixos = [
                {"name": "Daniel", "whatsapp": "(11) 9479-81529"},
                {"name": "Mateus", "whatsapp": "(11) 99190-5547"},
                {"name": "Leonel", "whatsapp": "(11) 91302-7842"},
                {"name": "Matheus", "whatsapp": "(11) 94887-6252"},
            ]
            contatos_adicionais = st.session_state["novos_contatos"]
            df_formatado = pd.concat([df_formatado, pd.DataFrame(contatos_fixos + contatos_adicionais)], ignore_index=True)

            st.success("Colunas selecionadas com sucesso!")
            st.subheader("Pré-visualização:")
            st.dataframe(df_formatado)

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
