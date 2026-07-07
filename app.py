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
        
        # Lupa de pesquisa por placa e filtro de tipo lado a lado
        col_pesquisa, col_filtro = st.columns([2, 1])
        with col_pesquisa:
            pesquisa_placa = st.text_input("🔍 Pesquisar por Placa", placeholder="Digite a placa do veículo...").upper().strip()
        with col_filtro:
            filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos", "Carro", "Caminhão"])
        
        # Aplicação dos filtros no DataFrame de exibição
        df_filtrado = df_frota.copy()
        if filtro_tipo != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Tipo"] == filtro_tipo]
        if pesquisa_placa:
            df_filtrado = df_filtrado[df_filtrado["Placa"].str.contains(pesquisa_placa, na=False)]
            
        st.dataframe(df_filtrado, use_container_width=True)

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
        
        # Puxa os dados antigos/atuais do veículo selecionado
        dados_veiculo = df_frota[df_frota["Placa"] == placa_selecionada].iloc[0]
        
        st.markdown(f"**Veículo Selecionado:** {dados_veiculo['Tipo']} - {dados_veiculo['Modelo']}")
        
        opcao_atualizacao = st.radio("O que deseja fazer?", ["Registrar Nova Troca de Óleo", "Corrigir/Editar Dados do Veículo (Se errou algo)"])
        
        with st.form("form_atualizar"):
            if opcao_atualizacao == "Registrar Nova Troca de Óleo":
                st.info("Ao confirmar, o sistema atualizará o KM Atual somando 5.000 KM automaticamente e agendará a próxima troca.")
                
                # Exibe o KM que servirá de base (o KM Atual antigo)
                km_base_troca = st.number_input("KM base para realizar a troca", value=int(dados_veiculo["KM Atual"]), min_value=0, step=1)
                
                # Avança o KM Atual em 5.000 KM (ex: 170.478 vira 175.478)
                novo_km_atual = km_base_troca + 5000
                # Calcula a próxima troca adicionando mais 5.000 KM (ex: vira 180.478)
                proxima_troca_nova = novo_km_atual + 5000
                
                if st.form_submit_button("Confirmar Nova Troca"):
                    df_frota.loc[df_frota["Placa"] == placa_selecionada, "KM Atual"] = novo_km_atual
                    df_frota.loc[df_frota["Placa"] == placa_selecionada, "Última Troca (KM)"] = novo_km_atual
                    df_frota.loc[df_frota["Placa"] == placa_selecionada, "Próxima Troca (KM)"] = proxima_troca_nova
                    
                    st.session_state.df_frota = df_frota
                    salvar_dados(df_frota)
                    st.success(f"Troca de óleo realizada! O veículo mudou para o KM Atual: {novo_km_atual} KM. Próxima troca agendada para: {proxima_troca_nova} KM.")
                    st.rerun()

            elif opcao_atualizacao == "Corrigir/Editar Dados do Veículo (Se errou algo)":
                st.warning("Modo Edição Livre: Altere os valores abaixo para corrigir erros passados.")
                
                # Resgata o índice da lista de tipos correspondente ao atual
                lista_tipos = ["Carro", "Caminhão"]
                idx_tipo = lista_tipos.index(dados_veiculo["Tipo"]) if dados_veiculo["Tipo"] in lista_tipos else 0
                
                col_edit_tipo, col_edit_mod = st.columns(2)
                with col_edit_tipo:
                    tipo_editado = st.selectbox("Tipo de Veículo", lista_tipos, index=idx_tipo)
                with col_edit_mod:
                    modelo_editado = st.text_input("Modelo do Veículo", value=str(dados_veiculo["Modelo"]))
                    
                col_edit_km, col_edit_ult, col_edit_prox = st.columns(3)
                with col_edit_km:
                    km_atual_editada = st.number_input("KM Atual", value=int(dados_veiculo["KM Atual"]), min_value=0, step=1)
                with col_edit_ult:
                    km_ult_editada = st.number_input("Última Troca (KM)", value=int(dados_veiculo["Última Troca (KM)"]), min_value=0, step=1)
                with col_edit_prox:
                    km_prox_editada = st.number_input("Próxima Troca (KM)", value=int(dados_veiculo["Próxima Troca (KM)"]), min_value=0, step=1)
                
                if st.form_submit_button("Salvar Alterações Corrigidas"):
                    if modelo_editado:
                        df_frota.loc[df_frota["Placa"] == placa_selecionada, "Tipo"] = tipo_editado
                        df_frota.loc[df_frota["Placa"] == placa_selecionada, "Modelo"] = modelo_editado
                        df_frota.loc[df_frota["Placa"] == placa_selecionada, "KM Atual"] = km_atual_editada
                        df_frota.loc[df_frota["Placa"] == placa_selecionada, "Última Troca (KM)"] = km_ult_editada
                        df_frota.loc[df_frota["Placa"] == placa_selecionada, "Próxima Troca (KM)"] = km_prox_editada
                        
                        st.session_state.df_frota = df_frota
                        salvar_dados(df_frota)
                        st.success("Dados do veículo corrigidos e salvos!")
                        st.rerun()
                    else:
                        st.error("O modelo do veículo não pode ficar em branco.")
