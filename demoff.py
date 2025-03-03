import streamlit as st
import pandas as pd
import openai  # OpenAI API
import matplotlib.pyplot as plt
import textwrap
from io import BytesIO
from docx import Document

# Sidebar Navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose an app", ["Feature Analysis", "Report Generator"])

# OpenAI API Configuration
openai.api_key = "14560021aaf84772835d76246b53397a"
openai.api_base = "https://amrxgenai.openai.azure.com/"
openai.api_type = 'azure'
openai.api_version = '2024-02-15-preview'
deployment_name = 'gpt'

def analyze_chatbot(question, df):
    prompt = f"""
    Using the data provided below, analyze and respond to the following question:
    {df.to_string(index=False)}
    Question: {question}
    """
    response = openai.ChatCompletion.create(
        engine=deployment_name,
        messages=[{"role": "system", "content": "You are a data analyst expert."},
                  {"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response["choices"][0]["message"]["content"].strip()

def plot_trend(df, group_by_col, value_col, title):
    trend_data = df.groupby(group_by_col)[value_col].sum().reset_index()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(trend_data[group_by_col], trend_data[value_col], color="skyblue")
    plt.xticks(rotation=90, ha='right', fontsize=8)
    plt.title(title)
    plt.xlabel(group_by_col)
    plt.ylabel(value_col)
    plt.tight_layout()
    st.pyplot(fig)

if app_mode == "Feature Analysis":
    st.title("Feature Analysis with OpenAI")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.dataframe(df.head())
        
        required_columns = {"Feature", "Description"}
        if required_columns.issubset(set(df.columns)):
            st.success("File successfully uploaded and validated!")
            tab1, tab2 = st.tabs(["Analysis", "Chatbot"])
            
            with tab1:
                country_columns = [col for col in df.columns if col not in {"S.No", "Feature", "Description", "Common", "Remarks"}]
                analysis_results = []
                
                for country in country_columns:
                    country_features = df[["Feature", "Description", country]].dropna()
                    country_features = country_features[country_features[country].astype(str).str.lower() == "yes"]
                    
                    if not country_features.empty:
                        summary = analyze_chatbot(f"Summarize features for {country}", country_features)
                        analysis_results.append({"Country": country, "Summary": summary})
                        st.write(summary)
                
                if analysis_results:
                    results_df = pd.DataFrame(analysis_results)
                    st.dataframe(results_df)
                    st.download_button("Download Analysis Results", results_df.to_csv(index=False), "analysis_results.csv")
            
            with tab2:
                user_question = st.text_input("Ask a question about the analysis:", key="feature_chat_input")
                if user_question:
                    response = analyze_chatbot(user_question, df)
                    st.write(response)
                    st.rerun()
        else:
            st.error("The uploaded file must contain 'Feature' and 'Description' columns.")

elif app_mode == "Report Generator":
    st.title("Report Generator with OpenAI")
    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
    
    if "search_history" not in st.session_state:
        st.session_state.search_history = []
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, encoding="latin1")
            st.dataframe(df.head())
        except UnicodeDecodeError:
            st.error("The uploaded file has an unsupported encoding. Please save it as UTF-8.")
        except Exception as e:
            st.error(f"Error processing the file: {e}")
        else:
            required_columns = {"Partner Id", "Last Name", "Paid As Position", "Gender", "Date of Birth", "Manager Name", "Recruiter Name", "Paid As", "Personal Sales Unit(PSU)", "Team Units(TU)", "First Name", "Adhoc Payment(ADP)", "Recruitment Commission Bonus (RCB)", "Basic commission Bonus(BCB)", "Super Commission Bonus(SCB)", "Performance Bonus (PCB)", "Gross Earnings"}
            
            if required_columns.issubset(set(df.columns)):
                st.success("File successfully uploaded and validated!")
                tab1, tab2 = st.tabs(["Analysis", "Chatbot"])
                
                with tab1:
                    analysis_options = [
                        ("Role-wise Gross Earnings", "Paid As Position", "Gross Earnings"),
                        ("Total Bonus Distribution", "Paid As Position", "Basic commission Bonus(BCB)"),
                        ("Performance Bonus by Position", "Paid As Position", "Performance Bonus (PCB)"),
                        ("Recruitment Commission Analysis", "Recruiter Name", "Recruitment Commission Bonus (RCB)"),
                        ("Manager-wise Bonus Distribution", "Manager Name", "Gross Earnings"),
                        ("Personal Sales Contribution", "First Name", "Personal Sales Unit(PSU)"),
                        ("Team Units Contribution", "First Name", "Team Units(TU)"),
                        ("Adhoc Payments Analysis", "First Name", "Adhoc Payment(ADP)"),
                        ("Gender-Based Earnings", "Gender", "Gross Earnings"),
                        ("Bonus Comparison by Gender", "Gender", "Basic commission Bonus(BCB)")
                    ]
                    
                    for title, group_by, value in analysis_options:
                        st.subheader(title)
                        plot_trend(df, group_by, value, title)
                
                with tab2:
                    predefined_questions = [
                        "Overall Bonus Analysis",
                        "Role wise bonus analysis with Total Bonus earned",
                        "Top Performers analysis - Total (Gross earnings)",
                        "Top Performers analysis - Individual Bonuses",
                        "Bottom Performers analysis - Total (Gross earnings)",
                        "Bottom Performers analysis - Individual Bonuses",
                        "Gender Wise Analysis"
                    ]
                    selected_question = st.selectbox("Choose a predefined question:", [""] + predefined_questions, key="predefined_question")
                    user_question = st.text_input("Or enter your own question:", key="report_chat_input")
                    if selected_question:
                        user_question = selected_question
                    if user_question:
                        response = analyze_chatbot(user_question, df)
                        st.session_state.search_history.insert(0, (user_question, response))
                        st.write("**Response:**", response)
                        st.rerun()
