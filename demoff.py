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
                    st.subheader("Chatbot - Insights, Trends, and Analysis")
                    user_question = st.text_input("Enter your question:")
                    
                    if user_question:
                        response = analyze_chatbot(user_question, df)
                        st.write("**Response:**", response)
                        
                        st.session_state.search_history.insert(0, {"question": user_question, "response": response})
                        
                    if st.session_state.search_history:
                        st.subheader("Search History")
                        for entry in st.session_state.search_history:
                            with st.expander(entry['question']):
                                st.write(entry['response'])
