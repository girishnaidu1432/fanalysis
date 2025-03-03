import streamlit as st
import pandas as pd
import openai  # OpenAI API
import matplotlib.pyplot as plt
from io import BytesIO

# Function to analyze chatbot queries with OpenAI
def analyze_chatbot(question, df):
    prompt = f"""
    Using the data provided below, analyze and respond to the following question:
    {df.to_string(index=False)}
    Question: {question}
    """
    response = openai.ChatCompletion.create(
        engine='gpt-4',
        messages=[{"role": "system", "content": "You are a data analyst expert."},
                  {"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response["choices"][0]["message"]["content"].strip()

# Function to plot trends
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

# Sidebar navigation
st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Choose an app", ["Feature Analysis", "Report Generator"])

# Feature Analysis Section
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
                    st.session_state.feature_chat_input = ""
        else:
            st.error("The uploaded file must contain 'Feature' and 'Description' columns.")

# Report Generator Section
elif app_mode == "Report Generator":
    st.title("Report Generator with OpenAI")
    uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

    # Initialize search history
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
            st.success("File successfully uploaded and validated!")
            tab1, tab2 = st.tabs(["Analysis", "Chatbot"])

            # Analysis tab
            with tab1:
                st.subheader("Visual Analysis")
                analysis_options = [
                    ("Role-wise Gross Earnings", "Paid As Position", "Gross Earnings"),
                    ("Gender-Based Earnings", "Gender", "Gross Earnings")
                ]
                for title, group_by, value in analysis_options:
                    st.subheader(title)
                    plot_trend(df, group_by, value, title)

            # Chatbot tab
            with tab2:
                st.subheader("Chatbot Analysis")

                # Ensure the input field is initialized
                if "report_chat_input" not in st.session_state:
                    st.session_state.report_chat_input = ""

                predefined_questions = [
                    "Overall Bonus Analysis",
                    "Top Performers analysis - Total (Gross earnings)"
                ]
                selected_question = st.selectbox("Choose a predefined question:", [""] + predefined_questions, key="predefined_question")

                # Input field for user question
                user_question = st.text_input("Or enter your own question:", key="report_chat_input")

                search_button = st.button("Search")

                if search_button or user_question:
                    if not user_question and selected_question:
                        user_question = selected_question
                    if user_question:
                        response = analyze_chatbot(user_question, df)
                        st.session_state.search_history.insert(0, (user_question, response))
                        st.write("**Response:**", response)

                        # Reset input field correctly
                        st.session_state.report_chat_input = ""

                # Display search history
                st.subheader("Search History")
                for question, answer in st.session_state.search_history:
                    with st.expander(question):
                        st.write(answer)
