import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Controle de Troca de Óleo", page_icon="🛢️", layout="wide")

# Nome do arquivo de banco de dados local
DB_FILE = "frota_oleo.csv"

# Função para carregar ou criar o banco de dados
def carregar_dados():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    else:
        # Cria um DataFrame vazio com as colunas necessárias se o arquivo não existir
        columns = [
            "Tipo", "Modelo", "Placa", "KM Atual", 
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

# Criando abas no Streamlit para organizar o sistema
aba_Painel, aba_Cadastro, aba_Atualizar = st.tabs(["📊 Painel da Frota", "➕ Cadastrar Veículo", "🔄 Atualizar KM / Troca"])

# --- ABA 1: PAINEL DA FROTA ---
with aba_Painel:
    st.header("Status Atual da Frota")
    
    if df_frota.empty:
        st.info("Nenhum veículo cadastrado ainda. Vá na aba 'Cadastrar Veículo'.")
    else:
        # Lógica para definir o Status baseado na KM
        # Se faltar menos de 1000km ou já passou, avisa
        status_list = []
        for idx, row in df_frota.iterrows():
            restante = row["Próxima Troca (KM)"] - row["KM Atual"]
            if restante <= 0:
                status_list.append("🔴 TROCA VENCIADA")
            elif restante <= 1000:
                status_list.append("🟡 TROCAR EM BREVE")
            else:
                status_list.append("🟢 OK")
        
        df_frota["Status"] = status_list
        salvar_dados(df_frota) # Atualiza o arquivo físico

        # Métricas rápidas
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Veículos", len(df_frota))
        col2.metric("Trocas Vencidas (🔴)", len(df_frota[df_frota["Status"] == "🔴 TROCA VENCIADA"]))
        col3.metric("Atenção (🟡)", len(df_frota[df_frota["Status"] == "🟡 TROCAR EM BREVE"]))

        st.markdown("---")
        
        # Filtro de visualização
        filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos", "Carro", "Caminhão"])
        if filtro_tipo != "Todos":
            st.dataframe(df_frota[df_frota["Tipo"] == filtro_tipo], use_container_width=True)
        else:
            st.dataframe(df_frota, use_container_width=True)

# --- ABA 2: CADASTRAR VEÍCULO ---
with aba_Cadastro:
    st.header("Adicionar Novo Veículo à Frota")
    
    with st.form("form_cadastro", clear_on_submit=True):
        col_tipo, col_mod, col_placa = st.columns(3)
        
        with col_tipo:
            tipo = st.selectbox("Tipo de Veículo", ["Carro", "Caminhão"])
        with col_mod:
            modelo = st.text_input("Modelo do Veículo (ex: Fiat Uno, 17180)", placeholder="Ex: Caminhão 17180")
        with col_placa:
            placa = st.text_input("Placa do Veículo", placeholder="ABC1D23").upper().strip()
            
        col_km_atual, col_km_troca, col_km_prox = st.columns(3)
        with col_km_atual:
            km_atual = st.number_input("Quilometragem Atual", min_value=0, step=1)
        with col_km_troca:
            km_ultima_troca = st.number_input("KM da Última Troca", min_value=0, step=1)
        with col_km_prox:
            km_proxima_troca = st.number_input("KM da Próxima Troca", min_value=0, step=1)
            
        botao_cadastrar = st.form_submit_button("Salvar Veículo")
        
        if botao_cadastrar:
            if modelo and placa:
                # Verificar se a placa já existe
                if placa in df_frota["Placa"].values:
                    st.error(f"Erro: A placa {placa} já está cadastrada!")
                else:
                    # Novo registro
                    novo_veiculo = {
                        "Tipo": tipo,
                        "Modelo": modelo,
                        "Placa": placa,
                        "KM Atual": km_atual,
                        "Última Troca (KM)": km_ultima_troca,
                        "Próxima Troca (KM)": km_proxima_troca,
                        "Status": "Calculando..."
                    }
                    
                    df_frota = pd.concat([df_frota, pd.DataFrame([novo_veiculo])], ignore_index=True)
                    st.session_state.df_frota = df_frota
                    salvar_dados(df_frota)
                    st.success(f"Veículo {modelo} [{placa}] cadastrado com sucesso!")
                    st.rerun()
            else:
                st.warning("Por favor, preencha o Modelo e a Placa.")

# --- ABA 3: ATUALIZAR KM / TROCA ---
with aba_Atualizar:
    st.header("Atualizar Dados de Veículo Existente")
    
    if df_frota.empty:
        st.info("Nenhum veículo disponível para atualização.")
    else:
        # Selecionar o veículo pela placa
        lista_veiculos = df_frota["Placa"].tolist()
        placa_selecionada = st.selectbox("Selecione a Placa do Veículo", lista_veiculos)
        
        # Puxa os dados atuais do veículo selecionado
        dados_veiculo = df_frota[df_frota["Placa"] == placa_selecionada].iloc[0]
        
        st.markdown(f"**Veículo Selecionado:** {dados_veiculo['Tipo']} - {dados_veiculo['Modelo']}")
        
        opcao_atualizacao = rádio = st.radio("O que deseja fazer?", ["Apenas Atualizar KM Atual", "Registrar Nova Troca de Óleo"])
        
        with st.form("form_atualizar"):
            if opcao_atualizacao == "Apenas Atualizar KM Atual":
                nova_km = st.number_input("Nova KM Atual", min_value=int(dados_veiculo["KM Atual"]), step=1)
                
                if st.form_submit_button("Atualizar KM"):
                    df_frota.loc[df_frota["Placa"] == placa_selecionada, "KM Atual"] = nova_km
                    st.session_state.df_frota = df_frota
                    salvar_dados(df_frota)
                    st.success("Quilometragem atualizada!")
                    st.rerun()
                    
            elif opcao_atualizacao == "Registrar Nova Troca de Óleo":
                st.info("Isso atualizará a KM da última troca e definirá a próxima troca.")
                km_troca_feita = st.number_input("KM em que a troca foi feita", min_value=int(dados_veiculo["Última Troca (KM)"]), step=1)
                proxima_troca_nova = st.number_input("Nova KM para próxima troca", min_value=int(km_troca_feita), step=1)
                
                if st.form_submit_button("Confirmar Nova Troca"):
                    df_frota.loc[df_frota["Placa"] == placa_selecionada, "KM Atual"] = km_troca_feita
                    df_frota.loc[df_frota["Placa"] == placa_selecionada, "Última Troca (KM)"] = km_troca_feita
                    df_frota.loc[df_frota["Placa"] == placa_selecionada, "Próxima Troca (KM)"] = proxima_troca_nova
                    
                    st.session_state.df_frota = df_frota
                    salvar_dados(df_frota)
                    st.success("Troca de óleo registrada com sucesso!")
                    st.rerun()
