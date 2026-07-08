import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuração da página (Tema Escuro/Claro nativo do Streamlit se adapta perfeitamente)
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

# --- CABEÇALHO DO SISTEMA ---
with st.container():
    col_titulo, col_status = st.columns([4, 1])
    with col_titulo:
        st.title("🛢️ Sistema de Monitoramento e Controle de Troca de Óleo")
        st.markdown("_Gerenciamento inteligente e controle preventivo de quilometragem da frota empresarial._")
    with col_status:
        st.caption("Status do Sistema")
        st.success("Banco de Dados Online")

st.divider()

# Criando abas com visual limpo
aba_Painel, aba_Cadastro, aba_Atualizar = st.tabs(["📊 Painel da Frota", "➕ Cadastrar Veículo", "🔄 Atualizar KM / Troca"])

# --- ABA 1: PAINEL DA FROTA ---
with aba_Painel:
    st.subheader("Painel de Controle e Status")
    
    if df_frota.empty:
        st.info("Nenhum veículo cadastrado ainda. Vá na aba 'Cadastrar Veículo'.")
    else:
        # Lógica de definição de Status
        status_list = []
        for idx, row in df_frota.iterrows():
            restante = row["Próxima Troca (KM)"] - row["KM Atual"]
            if restante <= 0: status_list.append("🔴 TROCA VENCIDA")
            elif restante <= 1000: status_list.append("🟡 TROCAR EM BREVE")
            else: status_list.append("🟢 OK")
        df_frota["Status"] = status_list
        salvar_dados(df_frota)
        
        # Área de Indicadores (Métricas em Cards com Bordas)
        col1, col2, col3 = st.columns(3)
        with col1:
            with st.container(border=True):
                st.metric("Frota Total", f"{len(df_frota)} veíc.")
        with col2:
            with st.container(border=True):
                st.metric("Trocas Vencidas", f"{len(df_frota[df_frota['Status'] == '🔴 TROCA VENCIDA'])} u.", delta_color="inverse")
        with col3:
            with st.container(border=True):
                st.metric("Atenção / Alerta", f"{len(df_frota[df_frota['Status'] == '🟡 TROCAR EM BREVE'])} u.")
        
        st.divider()
        
        # Filtros de Busca Avançada
        with st.container(border=True):
            st.markdown("**Filtros de Pesquisa**")
            col_pesquisa, col_filtro = st.columns([3, 1])
            with col_pesquisa:
                pesquisa_termo = st.text_input("Buscar Veículo", placeholder="Digite a placa por completo ou o nome do responsável...", label_visibility="collapsed").strip()
            with col_filtro:
                filtro_tipo = st.selectbox("Tipo", ["Todos", "Carro", "Caminhão"], label_visibility="collapsed")
        
        # Filtragem dos dados
        df_filtrado = df_frota.copy()
        if filtro_tipo != "Todos":
            df_filtrado = df_filtrado[df_filtrado["Tipo"] == filtro_tipo]
            
        if pesquisa_termo:
            mask = (df_filtrado["Placa"].str.contains(pesquisa_termo.upper(), na=False) | df_filtrado["Responsável"].str.contains(pesquisa_termo, case=False, na=False))
            df_filtrado = df_filtrado[mask]
            st.markdown(f"**Resultados da pesquisa para '{pesquisa_termo}':**")
        else:
            df_filtrado = df_filtrado.head(3)
            st.markdown("**Exibindo registros recentes (use a barra de busca acima para ver toda a frota):**")
            
        # Tabela Formatada de Alta Visibilidade
        st.dataframe(df_filtrado, use_container_width=True)

# --- ABA 2: CADASTRAR VEÍCULO ---
with aba_Cadastro:
    st.subheader("Inserir Novo Ativo na Frota")
    
    with st.container(border=True):
        with st.form("form_cadastro", clear_on_submit=True):
            st.markdown("### Dados Cadastrais do Veículo")
            col_resp, col_tipo, col_mod, col_placa = st.columns(4)
            
            responsavel = col_resp.selectbox("Responsável Técnico", RESPONSAVEIS)
            tipo = col_tipo.selectbox("Tipo de Veículo", ["Carro", "Caminhão"])
            modelo = col_mod.text_input("Modelo do Veículo", placeholder="Ex: Caminhão 17180")
            placa = col_placa.text_input("Placa do Veículo (Mercosul/Antiga)", placeholder="ABC1D23").upper().strip()
                
            st.markdown("### Controle de Rodagem (Quilometragem)")
            col_km_a, col_km_t = st.columns(2)
            km_atual = col_km_a.number_input("Quilometragem Atual do Painel (KM)", min_value=0, step=1)
            km_ultima = col_km_t.number_input("Quilometragem da Última Troca (KM)", min_value=0, step=1)
                
            st.markdown("<br>", unsafe_allow_html=True)
            botao_cadastrar = st.form_submit_button("💾 Salvar Registro de Veículo", use_container_width=True)
            
            if botao_cadastrar:
                if modelo and placa:
                    if placa in df_frota["Placa"].values:
                        st.error(f"❌ Erro de Duplicidade: A placa **{placa}** já se encontra cadastrada no banco de dados!")
                    else:
                        # Validação de regras de limite por responsável
                        veiculos_do_resp = df_frota[df_frota["Responsável"] == responsavel]
                        qtd_carros = len(veiculos_do_resp[veiculos_do_resp["Tipo"] == "Carro"])
                        qtd_caminhoes = len(veiculos_do_resp[veiculos_do_resp["Tipo"] == "Caminhão"])
                        
                        if tipo == "Carro" and qtd_carros >= 1:
                            st.error(f"⚠️ Limite Atingido: {responsavel} já possui 1 Carro vinculado sob sua responsabilidade.")
                        elif tipo == "Caminhão" and qtd_caminhoes >= 2:
                            st.error(f"⚠️ Limite Atingido: {responsavel} já possui 2 Caminhões vinculados sob sua responsabilidade.")
                        else:
                            km_proxima_troca = km_ultima + 5000
                            novo_veiculo = {
                                "Tipo": tipo, "Modelo": modelo, "Placa": placa, 
                                "Responsável": responsavel, "KM Atual": km_atual, 
                                "Última Troca (KM)": km_ultima, "Próxima Troca (KM)": km_proxima_troca, 
                                "Status": "Calculando..."
                            }
                            df_frota = pd.concat([df_frota, pd.DataFrame([novo_veiculo])], ignore_index=True)
                            st.session_state.df_frota = df_frota
                            salvar_dados(df_frota)
                            st.success(f"✅ Veículo {modelo} [{placa}] registrado com sucesso para {responsavel}! Próxima troca projetada para {km_proxima_troca} KM.")
                            st.rerun()
                else:
                    st.warning("⚠️ Atenção: Preencha obrigatoriamente os campos de 'Modelo' e 'Placa' para prosseguir.")

# --- ABA 3: ATUALIZAR KM / TROCA ---
with aba_Atualizar:
    st.subheader("Painel de Manutenção e Retificação")
    
    if df_frota.empty:
        st.info("Nenhum veículo disponível para atualização no momento.")
    else:
        with st.container(border=True):
            st.markdown("### 🔍 Identificar Veículo")
            termo_at = st.text_input("Pesquise por Placa ou Responsável para desbloquear o formulário", key="busca_at", placeholder="Digite e pressione Enter...").strip()
        
        if termo_at:
            df_at = df_frota[df_frota["Placa"].str.contains(termo_at.upper(), na=False) | df_frota["Responsável"].str.contains(termo_at, case=False, na=False)]
            if not df_at.empty:
                st.markdown("**Veículos localizados:**")
                st.dataframe(df_at, use_container_width=True, key="tabela_at")
                
                col_sel, col_acao = st.columns([2, 2])
                with col_sel:
                    opcoes = [f"{row['Placa']} - {row['Modelo']} ({row['Responsável']})" for _, row in df_at.iterrows()]
                    selecao = st.selectbox("Selecione o veículo exato para a operação:", opcoes, key="sel_veiculo")
                    placa_selecionada = selecao.split(" - ")[0]
                    dados = df_frota[df_frota["Placa"] == placa_selecionada].iloc[0]
                
                with col_acao:
                    tipo_acao = st.radio("Selecione a operação desejada:", ["🔄 Registrar Nova Troca de Óleo", "✏️ Editar / Corrigir Dados Cadastrais"], index=0)
                
                st.divider()
                
                # Operação 1: Troca de Óleo
                if tipo_acao == "🔄 Registrar Nova Troca de Óleo":
                    with st.form("form_troca"):
                        st.markdown(f"#### Registro de Manutenção Preventiva: **[{placa_selecionada}]**")
                        st.info("Ao confirmar, o sistema assume que uma nova manutenção foi efetuada, avançará a quilometragem atual e estenderá a próxima troca automaticamente em 5.000 KM.")
                        
                        km_base_troca = st.number_input("Confirmar Quilometragem de Entrada da Troca:", value=int(dados["KM Atual"]), min_value=0, step=1)
                        
                        novo_km_atual = km_base_troca + 5000
                        proxima_troca_nova = novo_km_atual + 5000
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.form_submit_button("🚀 Finalizar e Validar Nova Troca", use_container_width=True):
                            df_frota.loc[df_frota["Placa"] == placa_selecionada, "KM Atual"] = novo_km_atual
                            df_frota.loc[df_frota["Placa"] == placa_selecionada, "Última Troca (KM)"] = novo_km_atual
                            df_frota.loc[df_frota["Placa"] == placa_selecionada, "Próxima Troca (KM)"] = proxima_troca_nova
                            
                            st.session_state.df_frota = df_frota
                            salvar_dados(df_frota)
                            st.success(f"🎉 Troca computada! KM Atualizado para {novo_km_atual} KM e Próxima Manutenção estendida para {proxima_troca_nova} KM.")
                            st.rerun()
                            
                # Operação 2: Edição / Correção de dados de forma isolada
                else:
                    with st.form("form_edicao"):
                        st.markdown(f"#### Retificação de Cadastro: **[{placa_selecionada}]**")
                        st.warning("Utilize esta seção apenas se tiver digitado alguma informação incorretamente no cadastro inicial do veículo.")
                        
                        col_e1, col_e2, col_e3 = st.columns(3)
                        new_mod = col_e1.text_input("Corrigir Nome/Modelo", value=dados["Modelo"])
                        new_resp = col_e2.selectbox("Alterar Responsável", RESPONSAVEIS, index=RESPONSAVEIS.index(dados["Responsável"]))
                        new_km = col_e3.number_input("Ajustar KM Atual do Painel", value=int(dados["KM Atual"]), min_value=0, step=1)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.form_submit_button("💾 Gravar Correções", use_container_width=True):
                            df_frota.loc[df_frota["Placa"] == placa_selecionada, ["Responsável", "Modelo", "KM Atual"]] = [new_resp, new_mod, new_km]
                            st.session_state.df_frota = df_frota
                            salvar_dados(df_frota)
                            st.success("✅ Informações do veículo retificadas e salvas com sucesso no banco de dados!")
                            st.rerun()
            else:
                st.error(f"❌ Nenhum veículo correspondente localizado para a busca '{termo_at}'. Verifique a grafia.")
        else:
            st.info("💡 Pronto para busca: Digite a placa ou o nome do responsável no campo acima e tecle Enter para carregar os controles de manutenção.")
