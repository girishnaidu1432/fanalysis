import streamlit as st
import pandas as pd
import openai  # OpenAI API
import matplotlib.pyplot as plt
from io import BytesIO

# OpenAI API Configuration
openai.api_key = "14560021aaf84772835d76246b53397a"
openai.api_base = "https://amrxgenai.openai.azure.com/"
openai.api_type = 'azure'
openai.api_version = '2024-02-15-preview'
deployment_name = 'gpt'

def analyze_chatbot(question, df, max_rows=30, max_columns=10):
    """
    Analyze a question using the GPT model, with controlled input size to prevent token overflow.
    """
    import pandas as pd

    # Truncate rows and columns
    df_limited = df.iloc[:max_rows, :max_columns].copy()

    # Add note for user
    note = (
        f"NOTE: Original dataset had {df.shape[0]} rows and {df.shape[1]} columns. "
        f"Only the first {max_rows} rows and first {max_columns} columns are used to prevent token overflow.\n\n"
    )

    # Convert truncated DataFrame to string
    df_text = df_limited.to_string(index=False)

    # Final prompt
    prompt = f"""
    You are an AI analyst. Given the structured dataset below, answer the user's question as clearly and accurately as possible.

    {note}
    Data Snapshot:
    {df_text}

    Question:
    {question}
    """

    # Call OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4-0125-preview",  # Or your model/deployment name
        messages=[
            {"role": "system", "content": "You are a helpful data analyst AI assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=1000  # response limit only
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

                st.markdown("#### 🤖 Ask our AI Analyst")

                categories = {
                    "📅 Month-wise / Trend Analysis": [
                        "Show month-wise total bonus distribution.",
                        "Compare earnings Month-on-Month for all branches.",
                        "What was the highest grossing month and why?",
                        "Which months showed consistent increase in bonuses?"
                    ],
                    "🧍 Consistent Performer (Participant)": [
                        "Who are the consistent top earners across all months?",
                        "List participants who received bonuses every month.",
                        "Who had the highest average earnings over time?"
                    ],
                    "🏢 Consistent Performer (Branch)": [
                        "Which branches had top consistent performance month-over-month?",
                        "Which branches saw a steady rise in bonuses?"
                    ],
                    "💰 Bonus Type Analysis": [
                        "How many types of bonuses are distributed?",
                        "Which bonus type contributes most to total earnings?",
                        "Month-wise trend of each bonus type.",
                        "Top 3 bonus types based on total distribution."
                    ]
                }

                selected_category = st.selectbox("Choose a question category", [""] + list(categories.keys()), key="category_select")

                predefined_question = ""
                if selected_category:
                    predefined_question = st.selectbox("Choose a predefined question", [""] + categories[selected_category], key="predefined_question_select")

                user_question = st.text_input("Or ask your own question:", key="report_chat_input")

                if st.button("Search"):
                    final_question = user_question or predefined_question
                    if final_question:
                        st.markdown(f"🔍 **Question Asked:** {final_question}")
                        response = analyze_chatbot(final_question, df)
                        st.session_state.search_history.insert(0, (final_question, response))
                        st.write("💡 **AI Response:**")
                        st.success(response)
                        st.session_state.report_chat_input = ""

                # Display search history
                st.subheader("🕒 Search History")
                for question, answer in st.session_state.search_history:
                    with st.expander(question):
                        st.write(answer)
