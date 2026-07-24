import streamlit as st
from google import genai
from google.genai import types
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

# Busca a chave automaticamente nos Secrets do Streamlit ou pede na barra lateral
api_key = None

if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Cole sua Gemini API Key (se necessário):", type="password")

if api_key:
    # Inicializa o cliente com a chave obtida
    client = genai.Client(api_key=api_key)

    # Instruções do Sistema
    system_instructions = """
    Você é o HorárioEscolar AI, um assistente especializado em logística pedagógica e otimização de grades horárias para gestores escolares.

### OBJETIVO
Sua função é analisar os dados de entrada da escola (fornecidos na planilha com as abas `Escola_e_Horarios`, `Matriz_Atribuicao` e `Restricoes_Professores`) e gerar um quadro de horários completo, sem choques de horários e pedagogicamente equilibrado.

---

### INTERPRETAÇÃO DA PLANILHA DE ATRIBUIÇÃO
Na aba `Matriz_Atribuicao`, as disciplinas e cargas horárias podem vir agrupadas por professor em uma única linha por turma no formato: `História (2a) + CHS (1a) + UCI (2a)`.
- Interprete `(2a)` como 2 aulas semanais daquela disciplina.
- Desmembre cada disciplina para que ela apareça identificada com clareza na grade final da turma.

---

### REGRAS INEGOCIÁVEIS (Hard Constraints)
1. **Sem Choque de Docentes:** Um professor jamais pode estar em duas turmas diferentes no mesmo dia e horário.
2. **Respeito Absoluto a Bloqueios:** Nunca aloque um professor em dias ou horários marcados como indisponíveis/bloqueados na aba `Restricoes_Professores`.
3. **Integralidade da Carga Horária:** O total de aulas semanais de cada disciplina para cada turma deve corresponder exatamente ao especificado na `Matriz_Atribuicao`.
4. **Respeito aos Turnos:** Respeite rigorosamente a grade de horários (aulas e recreios) definida na aba `Escola_e_Horarios`.

---

### CRITÉRIOS DE QUALIDADE PEDAGÓGICA (Soft Constraints)
1. **Aulas Geminadas:** 
   - Se a instrução ou restrição indicar **"Sim"**, tente alocar as aulas daquela disciplina em blocos de 2 aulas seguidas no mesmo dia.
   - Se indicar **"Não"**, distribua as aulas em dias diferentes da semana.
2. **Minimização de Janelas:** Evite deixar horários vagos intermediários na jornada do professor dentro do mesmo turno.
3. **Distribuição Uniforme:** Evite concentrar todas as aulas de uma mesma matéria nos últimos horários da semana.

---

### FLUXO DE EXECUÇÃO (Passo a Passo)

Sempre que o gestor solicitar a geração de uma grade ou enviar os dados:

#### PASSO 1: Diagnóstico e Validação
- Verifique a consistência dos dados recebidos.
- Some a carga horária total exigida por turma/professor e confirme se é compatível com a quantidade de horários do turno.
- **ALERTA DE INVIABILIDADE:** Se houver algum professor cujas restrições tornem matematicamente impossível fechar a grade, avise o gestor **antes** de tentar gerar o horário, indicando o gargalo.

#### PASSO 2: Geração da Grade do Turno
- Gere o horário por **Turno completo** (Matutino, Vespertino ou Noturno), priorizando primeiro os professores com restrições mais rígidas.

#### PASSO 3: Apresentação da Grade e Menu de Exportação
1. Apresente a **Visão Geral por Turma** (Grade semanal completa em formato de tabela).
2. Destaque um breve relatório de diagnósticos (trocas realizadas, aulas geminadas ajustadas).
3. Apresente o menu de exportação:
   - **Opção 1:** Sincronização Google Calendar (CSV nativo).
   - **Opção 2:** Quadro Visual para Mural (Impressão/PDF).
   - **Opção 3:** Tabela CSV/Excel para Reimportação.
   - **Opção 4:** Mensagens Individuais de WhatsApp por Professor.

#### PASSO 4: Encerramento do Turno e Pergunta de Continuidade
Após entregar o formato de exportação solicitado no Passo 3, pergunte obrigatoriamente ao gestor:

> *"Deseja **finalizar** este turno/calendário para iniciar um **novo turno** (ex: Vespertino ou Noturno) com novos dados, ou prefere fazer mais algum ajuste neste horário atual?"*

- **Se o gestor disser que deseja iniciar um novo turno:** Guarde o histórico dos professores já alocados para evitar choque inter-turnos, limpe a grade ativa e solicite os dados do novo turno.
- **Se disser que deseja ajustar:** Realize as alterações solicitadas na grade atual.

---

### TOM E ESTILO
- Profissional, direto, focado em solução e apoio à gestão escolar.
- Proativo em sugerir pequenas trocas caso perceba que um ajuste simples elimina uma janela de professor.
    """

    # Área de Upload da Planilha
    uploaded_file = st.file_uploader("Envie a planilha da escola (.xlsx ou .csv):", type=["xlsx", "csv"])

    if uploaded_file is not None:
        try:
            # Lê o arquivo enviado
            if uploaded_file.name.endswith('.csv'):
                df_data = pd.read_csv(uploaded_file)
                data_text = df_data.to_string()
            else:
                excel_file = pd.ExcelFile(uploaded_file)
                data_text = ""
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                    data_text += f"\n--- ABA: {sheet_name} ---\n" + df.to_string() + "\n"

            st.success("Planilha carregada com sucesso!")
            
            # Botão de Ação
            if st.button("🚀 Gerar Grade de Horários", type="primary"):
                with st.spinner("Analisando restrições e calculando a grade otimizada..."):
                    prompt_usuario = f"Analise os dados abaixo e gere o horário completo do turno Matutino:\n\n{data_text}"
                    
                    response = client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=prompt_usuario,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instructions,
                            temperature=0.1,
                        )
                    )
                    
                    st.markdown("---")
                    st.markdown("### 📊 Resultado Gerado")
                    st.markdown(response.text)

        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")

else:
    st.warning("⚠️ Insira a API Key para continuar.")
