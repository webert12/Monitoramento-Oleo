import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Controle de Troca de Óleo", page_icon="🛢️", layout="wide")

# Nome do arquivo de banco de dados local
DB_FILE = "frota_oleo.csv"

# Lista de Responsáveis (Turmas)
RESPONSAVEIS = ["Ednaldo", "Rafael", "Luiz Felipe", "Cardoso", "Guilherme", "Paulo", "Everaldo"]

# Função para carregar ou criar o banco de dados
def carregar_dados():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # Garantir que as colunas necessárias existam
        if "Responsável" not in df.columns:
            df.insert(3, "Responsável", "Não Definido")
        if "Modelo" not in df.columns:
            df.insert(1, "Modelo", "Não Informado")
        return df
    else:
        columns = [
            "Tipo", "Modelo", "Placa", "Responsável", "KM Atual", 
            "Última Troca (KM)", "Próxima Troca (KM)", "Status"
        ]
        return pd.DataFrame(columns=columns)

# Função para salvar os dados
def salvar_dados(df):
    df.to_csv(DB_FILE, index=False)

# Inicializa os dados na sessão do Streamlit
if 'df_frota' not in st.session_state:
    st.session_state.df_frota = carregar_dados()

df_frota = st.session_state.df_frota

# --- INTERFACE INICIAL ---
st.title("🛢️ Sistema de Monitoramento e Controle de Troca de Óleo")
st.markdown("Gerencie a frota de carros e caminhões da sua empresa de forma simples.")

# Criando abas
aba_Painel, aba_Cadastro, aba_Atualizar = st.tabs(["📊 Painel da Frota", "➕ Cadastrar Veículo", "🔄 Atualizar KM / Troca"])

# --- ABA 1: PAINEL DA FROTA ---
with aba_Painel:
    st.header("Status Atual da Frota")
    if df_frota.empty:
        st.info("Nenhum veículo cadastrado ainda.")
    else:
        status_list = []
        for idx, row in df_frota.iterrows():
            restante = row["Próxima Troca (KM)"] - row["KM Atual"]
            if restante <= 0: status_list.append("🔴 TROCA VENCIADA")
            elif restante <= 1000: status_list.append("🟡 TROCAR EM BREVE")
            else: status_list.append("🟢 OK")
        df_frota["Status"] = status_list
        salvar_dados(df_frota)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Veículos", len(df_frota))
        col2.metric("Trocas Vencidas (🔴)", len(df_frota[df_frota["Status"] == "🔴 TROCA VENCIADA"]))
        col3.metric("Atenção (🟡)", len(df_frota[df_frota["Status"] == "🟡 TROCAR EM BREVE"]))
        st.markdown("---")
        pesquisa_termo = st.text_input("🔍 Pesquisar por Placa ou Nome", placeholder="Digite a placa ou responsável...").strip()
        df_filtrado = df_frota.copy()
        if pesquisa_termo:
            mask = (df_filtrado["Placa"].str.contains(pesquisa_termo.upper(), na=False) | df_filtrado["Responsável"].str.contains(pesquisa_termo, case=False, na=False))
            df_filtrado = df_filtrado[mask]
        else:
            df_filtrado = df_filtrado.head(3)
        st.dataframe(df_filtrado, use_container_width=True)

# --- ABA 2: CADASTRAR VEÍCULO ---
with aba_Cadastro:
    st.header("Adicionar Novo Veículo à Frota")
    with st.form("form_cadastro", clear_on_submit=True):
        col_resp, col_tipo, col_mod, col_placa = st.columns(4)
        responsavel = col_resp.selectbox("Responsável", RESPONSAVEIS)
        tipo = col_tipo.selectbox("Tipo de Veículo", ["Carro", "Caminhão"])
        modelo = col_mod.text_input("Modelo do Veículo")
        placa = col_placa.text_input("Placa do Veículo").upper().strip()
        col_km_a, col_km_t = st.columns(2)
        km_atual = col_km_a.number_input("KM Atual", min_value=0, step=1)
        km_ultima = col_km_t.number_input("KM da Última Troca", min_value=0, step=1)
        if st.form_submit_button("Salvar Veículo"):
            if placa in df_frota["Placa"].values:
                st.error("Placa já cadastrada!")
            else:
                novo_veiculo = {"Tipo": tipo, "Modelo": modelo, "Placa": placa, "Responsável": responsavel, "KM Atual": km_atual, "Última Troca (KM)": km_ultima, "Próxima Troca (KM)": km_ultima + 5000, "Status": "OK"}
                df_frota = pd.concat([df_frota, pd.DataFrame([novo_veiculo])], ignore_index=True)
                st.session_state.df_frota = df_frota
                salvar_dados(df_frota)
                st.rerun()

# --- ABA 3: ATUALIZAR KM / TROCA ---
with aba_Atualizar:
    st.header("Atualizar / Corrigir Dados")
    termo_at = st.text_input("Buscar por Placa ou Responsável", key="busca_at").strip()
    
    if termo_at:
        df_at = df_frota[df_frota["Placa"].str.contains(termo_at.upper(), na=False) | df_frota["Responsável"].str.contains(termo_at, case=False, na=False)]
        if not df_at.empty:
            st.dataframe(df_at, use_container_width=True)
            placa_selecionada = st.selectbox("Selecione o Veículo (Placa)", df_at["Placa"].tolist())
            dados = df_frota[df_frota["Placa"] == placa_selecionada].iloc[0]
            
            tipo_acao = st.radio("Escolha a ação:", ["Registrar Nova Troca de Óleo", "Editar/Corrigir Dados Cadastrais"])
            
            if tipo_acao == "Registrar Nova Troca de Óleo":
                with st.form("form_troca"):
                    st.write(f"Atualizar Troca para: {dados['Modelo']} ({placa_selecionada})")
                    if st.form_submit_button("Confirmar Troca"):
                        df_frota.loc[df_frota["Placa"] == placa_selecionada, "KM Atual"] += 5000
                        df_frota.loc[df_frota["Placa"] == placa_selecionada, "Última Troca (KM)"] = df_frota.loc[df_frota["Placa"] == placa_selecionada, "KM Atual"]
                        df_frota.loc[df_frota["Placa"] == placa_selecionada, "Próxima Troca (KM)"] += 5000
                        st.session_state.df_frota = df_frota
                        salvar_dados(df_frota)
                        st.success("Troca registrada!")
                        st.rerun()
            else:
                with st.form("form_edicao"):
                    new_resp = st.selectbox("Responsável", RESPONSAVEIS, index=RESPONSAVEIS.index(dados["Responsável"]))
                    new_mod = st.text_input("Modelo", value=dados["Modelo"])
                    new_km = st.number_input("KM Atual", value=int(dados["KM Atual"]))
                    if st.form_submit_button("Salvar Edições"):
                        df_frota.loc[df_frota["Placa"] == placa_selecionada, ["Responsável", "Modelo", "KM Atual"]] = [new_resp, new_mod, new_km]
                        st.session_state.df_frota = df_frota
                        salvar_dados(df_frota)
                        st.success("Dados corrigidos com sucesso!")
                        st.rerun()
        else:
            st.warning("Nenhum veículo encontrado.")
    else:
        st.info("Digite um nome ou placa acima para começar a buscar.")
