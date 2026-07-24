import streamlit as st
import google.generativeai as genai
import pandas as pd

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Gerador de Horário Escolar AI",
    page_icon="🏫",
    layout="wide"
)

# Título e cabeçalho
st.title("🏫 Gerador Inteligente de Horário Escolar")
st.markdown("Faça o upload da planilha da sua escola para gerar a grade de horários otimizada com inteligência artificial.")

# Configuração da API Key (será configurada com segurança no Streamlit Cloud)
api_key = st.sidebar.text_input("Cole sua Gemini API Key (se necessário):", type="password")

if not api_key:
    # Tenta pegar das configurações salvas do servidor
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]

if api_key:
    genai.configure(api_key=api_key)

    # Definir as Instruções do Sistema
    system_instructions = """
    Você é o HorárioEscolar AI, um assistente especializado em logística pedagógica e otimização de grades horárias para gestores escolares.
    
    [COLE AQUI TODO O SEU PROMPT DAS INSTRUÇÕES DO SISTEMA QUE ESTRUTURAMOS ANTERIORMENTE]
    """

    # Configuração do Modelo Gemini com Thinking / Parâmetros
    generation_config = {
        "temperature": 0.1,
        "top_p": 0.95,
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config=generation_config,
        system_instruction=system_instructions
    )

    # Área de Upload da Planilha
    uploaded_file = st.file_uploader("Envie a planilha da escola (.xlsx ou .csv):", type=["xlsx", "csv"])

    if uploaded_file is not None:
        try:
            # Lê o arquivo enviado
            if uploaded_file.name.endswith('.csv'):
                df_data = pd.read_csv(uploaded_file)
                data_text = df_data.to_string()
            else:
                # Se for Excel com múltiplas abas
                excel_file = pd.ExcelFile(uploaded_file)
                data_text = ""
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                    data_text += f"\n--- ABA: {sheet_name} ---\n" + df.to_string() + "\n"

            st.success("Planilha carregada com sucesso!")
            
            # Botão de Ação
            if st.button("🚀 Gerar Grade de Horários", type="primary"):
                with st.spinner("Analisando restrições e calculando a grade otimizada... (Isso pode levar alguns segundos)"):
                    prompt_usuario = f"Analise os dados abaixo e gere o horário completo do turno Matutino:\n\n{data_text}"
                    response = model.generate_content(prompt_usuario)
                    
                    st.markdown("---")
                    st.markdown("### 📊 Resultado Gerado")
                    st.markdown(response.text)

        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")

else:
    st.warning("⚠️ Insira a API Key para continuar.")
