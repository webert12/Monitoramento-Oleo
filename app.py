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
        # Garantir que as colunas necessárias existam para não quebrar cadastros antigos
        if "Responsável" not in df.columns:
            df.insert(3, "Responsável", "Não Definido")
        if "Modelo" not in df.columns:
            df.insert(1, "Modelo", "Não Informado")
        return df
    else:
        # Cria um DataFrame vazio com as colunas necessárias se o arquivo não existir
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
        
        # Lupa de pesquisa por placa ou nome do responsável
        col_pesquisa, col_filtro = st.columns([2, 1])
        with col_pesquisa:
            pesquisa_termo = st.text_input("🔍 Pesquisar por Placa ou Nome", placeholder="Digite a placa ou responsável...").strip()
        with col_filtro:
            filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos", "Carro", "Caminhão"])
        
        # Aplicação dos filtros no DataFrame de exibição
        df_filtrado = df_frota.copy()
        
        if filtro_tipo != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Tipo"] == filtro_tipo]
            
        if pesquisa_termo:
            # Filtra por Placa ou Responsável se algo for digitado
            mask = (
                df_filtrado["Placa"].str.contains(pesquisa_termo.upper(), na=False) |
                df_filtrado["Responsável"].str.contains(pesquisa_termo, case=False, na=False)
            )
            df_filtrado = df_filtrado[mask]
        else:
            # Se não houver pesquisa, mostra apenas os 3 primeiros cadastrados para não poluir a tela
            df_filtrado = df_filtrado.head(3)
            
        st.dataframe(df_filtrado, use_container_width=True)

# --- ABA 2: CADASTRAR VEÍCULO ---
with aba_Cadastro:
    st.header("Adicionar Novo Veículo à Frota")
    
    with st.form("form_cadastro", clear_on_submit=True):
        col_resp, col_tipo, col_mod, col_placa = st.columns(4)
        
        with col_resp:
            responsavel = st.selectbox("Responsável", RESPONSAVEIS)
        with col_tipo:
            tipo = st.selectbox("Tipo de Veículo", ["Carro", "Caminhão"])
        with col_mod:
            modelo = st.text_input("Modelo do Veículo (ex: Fiat Uno, 17180)", placeholder="Ex: Caminhão 17180")
        with col_placa:
            placa = st.text_input("Placa do Veículo", placeholder="ABC1D23").upper().strip()
            
        # Alterado para 2 colunas, removendo a entrada manual da próxima troca
        col_km_atual, col_km_troca = st.columns(2)
        with col_km_atual:
            km_atual = st.number_input("Quilometragem Atual", min_value=0, step=1)
        with col_km_troca:
            km_ultima_troca = st.number_input("KM da Última Troca", min_value=0, step=1)
            
        botao_cadastrar = st.form_submit_button("Salvar Veículo")
        
        if botao_cadastrar:
            if modelo and placa:
                # Verificar se a placa já existe
                if placa in df_frota["Placa"].values:
                    st.error(f"Erro: A placa {placa} já está cadastrada!")
                else:
                    # Validar limite por responsável (2 Caminhões e 1 Carro)
                    veiculos_do_resp = df_frota[df_frota["Responsável"] == responsavel]
                    qtd_carros = len(veiculos_do_resp[veiculos_do_resp["Tipo"] == "Carro"])
                    qtd_caminhoes = len(veiculos_do_resp[veiculos_do_resp["Tipo"] == "Caminhão"])
                    
                    if tipo == "Carro" and qtd_carros >= 1:
                        st.error(f"Erro: {responsavel} já possui 1 Carro cadastrado. Limite atingido!")
                    elif tipo == "Caminhão" and qtd_caminhoes >= 2:
                        st.error(f"Erro: {responsavel} já possui 2 Caminhões cadastrados. Limite atingido!")
                    else:
                        # Cálculo automático da próxima troca somando 5.000 KM
                        km_proxima_troca = km_ultima_troca + 5000
                        
                        # Novo registro
                        novo_veiculo = {
                            "Tipo": tipo,
                            "Modelo": modelo,
                            "Placa": placa,
                            "Responsável": responsavel,
                            "KM Atual": km_atual,
                            "Última Troca (KM)": km_ultima_troca,
                            "Próxima Troca (KM)": km_proxima_troca,
                            "Status": "Calculando..."
                        }
                        
                        df_frota = pd.concat([df_frota, pd.DataFrame([novo_veiculo])], ignore_index=True)
                        st.session_state.df_frota = df_frota
                        salvar_dados(df_frota)
                        st.success(f"Veículo {modelo} [{placa}] cadastrado com sucesso para {responsavel}! Próxima troca projetada para {km_proxima_troca} KM.")
                        st.rerun()
            else:
                st.warning("Por favor, preencha o Modelo e a Placa.")

# --- ABA 3: ATUALIZAR KM / TROCA ---
with aba_Atualizar:
    st.header("Atualizar Dados de Veículo Existente")
    
    if df_frota.empty:
        st.info("Nenhum veículo disponível para atualização.")
    else:
        # Sistema Isolado de Busca por Placa ou Nome do Responsável
        st.markdown("### 🔍 Filtrar Veículo para Atualização")
        termo_busca_at = st.text_input("Buscar por Placa ou Nome do Responsável", placeholder="Digite a placa ou o nome do responsável...", key="termo_busca_atualizar").strip()
        
        # Filtra o dataframe localmente apenas para esta aba
        df_filtrado_at = df_frota.copy()
        if termo_busca_at:
            mask_at = (
                df_filtrado_at["Placa"].str.contains(termo_busca_at.upper(), na=False) |
                df_filtrado_at["Responsável"].str.contains(termo_busca_at, case=False, na=False)
            )
            df_filtrado_at = df_filtrado_at[mask_at]
            
            # Mostra a tabela isolada com os resultados encontrados na busca
            st.markdown("**Veículos encontrados:**")
            st.dataframe(df_filtrado_at, use_container_width=True, key="df_tabela_atualizar")
        
        if df_filtrado_at.empty:
            st.warning("Nenhum veículo correspondente encontrado para atualização.")
        else:
            # Monta as opções dinamicamente exibindo Placa, Modelo e Responsável no Selectbox
            opcoes_veiculos = [f"{row['Placa']} - {row['Modelo']} ({row['Responsável']})" for _, row in df_filtrado_at.iterrows()]
            veiculo_selecionado_str = st.selectbox("Selecione o Veículo Abaixo", opcoes_veiculos, key="selectbox_atualizar")
            
            # Extrai apenas a Placa real para buscar a linha correta no DataFrame original
            placa_selecionada = veiculo_selecionado_str.split(" - ")[0]
            
            # Puxa os dados antigos/atuais do veículo selecionado
            dados_veiculo = df_frota[df_frota["Placa"] == placa_selecionada].iloc[0]
            
            st.markdown(f"**Veículo Selecionado:** {dados_veiculo['Tipo']} - {dados_veiculo['Modelo']} [{placa_selecionada}] | **Responsável:** {dados_veiculo.get('Responsável', 'Não Definido')}")
            
            opcao_atualizacao = st.radio("O que deseja fazer?", ["Atualizar com Nova Troca de Óleo", "Corrigir/Editar Dados do Veículo (Se errou algo)"])
            
            with st.form("form_atualizar"):
                if opcao_atualizacao == "Atualizar com Nova Troca de Óleo":
                    st.info("Ao confirmar, o sistema atualizará o KM Atual e agendará a próxima troca automaticamente (+ 5.000 KM).")
                    
                    # Exibe o KM que servirá de base
                    km_base_troca = st.number_input("KM base para realizar a troca", value=int(dados_veiculo["KM Atual"]), min_value=0, step=1)
                    
                    # Avança o KM Atual em 5.000 KM e agenda a próxima
                    novo_km_atual = km_base_troca + 5000
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
                    
                    # Resgata o índice atual
                    lista_tipos = ["Carro", "Caminhão"]
                    idx_tipo = lista_tipos.index(dados_veiculo["Tipo"]) if dados_veiculo["Tipo"] in lista_tipos else 0
                    
                    resp_atual = dados_veiculo.get("Responsável", "Ednaldo")
                    idx_resp = RESPONSAVEIS.index(resp_atual) if resp_atual in RESPONSAVEIS else 0
                    
                    col_edit_tipo, col_edit_mod, col_edit_resp = st.columns(3)
                    with col_edit_tipo:
                        tipo_editado = st.selectbox("Tipo de Veículo", lista_tipos, index=idx_tipo)
                    with col_edit_mod:
                        modelo_editado = st.text_input("Modelo do Veículo", value=str(dados_veiculo.get("Modelo", "Não Informado")))
                    with col_edit_resp:
                        responsavel_editado = st.selectbox("Responsável", RESPONSAVEIS, index=idx_resp)
                        
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
                            df_frota.loc[df_frota["Placa"] == placa_selecionada, "Responsável"] = responsavel_editado
                            df_frota.loc[df_frota["Placa"] == placa_selecionada, "KM Atual"] = km_atual_editada
                            df_frota.loc[df_frota["Placa"] == placa_selecionada, "Última Troca (KM)"] = km_ult_editada
                            df_frota.loc[df_frota["Placa"] == placa_selecionada, "Próxima Troca (KM)"] = km_prox_editada
                            
                            st.session_state.df_frota = df_frota
                            salvar_dados(df_frota)
                            st.success("Dados do veículo corrigidos e salvos!")
                            st.rerun()
                        else:
                            st.error("O modelo do veículo não pode ficar em branco.")
