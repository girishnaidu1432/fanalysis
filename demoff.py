import streamlit as st
import pandas as pd
import openai  # OpenAI API
import matplotlib.pyplot as plt
import textwrap
from io import BytesIO
from docx import Document

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
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.pyplot(fig)

if app_mode == "Feature Analysis":
    st.title("Feature Analysis with OpenAI")
    st.write("File Upload")
    
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])
    
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        st.write("Uploaded Data Preview:")
        st.dataframe(df.head())
    
        required_columns = {"Feature", "Description"}
        if required_columns.issubset(set(df.columns)):
            st.success("File successfully uploaded and validated!")
    
            tab1, tab2 = st.tabs(["Analysis", "Chatbot"])
    
            with tab1:
                country_columns = [col for col in df.columns if col not in {"S.No", "Feature", "Description", "Common", "Remarks"}]
    
                analysis_results = []
    
                st.write("Analyzing requirements for each country...")
                for country in country_columns:
                    st.subheader(f"Analysis for {country}")
                    
                    country_features = df[["Feature", "Description", country]].dropna()
                    country_features = country_features[country_features[country].astype(str).str.lower() == "yes"]
    
                    if not country_features.empty:
                        summary = analyze_requirements(country_features, country)
                        analysis_results.append({"Country": country, "Summary": summary})
                        st.write(summary)
                    else:
                        st.write(f"No relevant features found for {country}.")
    
                if analysis_results:
                    results_df = pd.DataFrame(analysis_results)
                    st.write("Consolidated Analysis:")
                    st.dataframe(results_df)
    
                    st.subheader("Feature Availability by Country")
                    feature_counts = {country: df[country].str.lower().eq("yes").sum() for country in country_columns}
                    feature_counts_df = pd.DataFrame(list(feature_counts.items()), columns=["Country", "Feature Count"])
                    
                    fig, ax = plt.subplots()
                    ax.bar(feature_counts_df["Country"], feature_counts_df["Feature Count"], color="skyblue")
                    plt.xticks(rotation=45)
                    plt.ylabel("Number of Features Available")
                    plt.title("Feature Count by Country")
                    st.pyplot(fig)
    
                    st.download_button("Download Analysis Results", results_df.to_csv(index=False), "analysis_results.csv")
                else:
                    st.warning("No valid country-specific features were found for analysis.")
            
            with tab2:
                st.subheader("Chatbot - Ask Questions about the Analysis")
                user_question = st.text_input("Ask a question:")
                
                if user_question:
                    response = analyze_chatbot(user_question)
                    st.write(response)
        else:
            st.error("The uploaded file must contain 'Feature' and 'Description' columns.")

elif app_mode == "Report Generator":
    st.title("Bonus Analysis with OpenAI")
    st.write("Upload and analyze CSV data containing bonus-related details.")
    
    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])
    if "search_history" not in st.session_state:
        st.session_state.search_history = []
    
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file, encoding="latin1")
            st.write("Uploaded Data Preview:")
            st.dataframe(df.head())
        except UnicodeDecodeError:
            st.error("The uploaded file has an unsupported encoding. Please save it as UTF-8.")
        except Exception as e:
            st.error(f"Error processing the file: {e}")
        else:
            required_columns = {"Partner Id", "Last Name", "Paid As Position", "Gender", "Date of Birth", "Manager Name", "Recruiter Name", "Paid As", "Personal Sales Unit(PSU)", "Team Units(TU)", "First Name", "Adhoc Payment(ADP)", "Recruitment Commission Bonus (RCB)", "Basic commission Bonus(BCB)", "Super Commission Bonus(SCB)", "Performance Bonus (PCB)", "Gross Earnings"}
            if required_columns.issubset(set(df.columns)):
                st.success("File successfully uploaded and validated!")
