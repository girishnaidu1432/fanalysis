import streamlit as st
import pandas as pd
import openai
import matplotlib.pyplot as plt

# Set Streamlit page background
st.markdown(f"""
<style>
    .stApp {{
        background-image: url("https://e0.pxfuel.com/wallpapers/986/360/desktop-wallpaper-background-color-4851-background-color-theme-colorful-brown-color.jpg");
        background-attachment: fixed;
        background-size: cover;
    }}
</style>
""", unsafe_allow_html=True)

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
    fig, ax = plt.subplots()
    ax.bar(trend_data[group_by_col], trend_data[value_col], color="skyblue")
    plt.xticks(rotation=45)
    plt.title(title)
    plt.xlabel(group_by_col)
    plt.ylabel(value_col)
    st.markdown("<br><br>", unsafe_allow_html=True)  # Fix overlapping
    st.pyplot(fig)

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
                st.subheader("Basic Analysis")
                st.subheader("Role-wise Gross Earnings")
                plot_trend(df, "Paid As Position", "Gross Earnings", "Gross Earnings by Role")
                
                st.subheader("Total Bonus Distribution")
                plot_trend(df, "Paid As Position", "Basic commission Bonus(BCB)", "Total Bonus Distribution")
            
            with tab2:
                st.subheader("Chatbot - Insights, Trends, and Analysis")
                predefined_questions = [
                    "What insights on Bonus we can get from this data?",
                    "Why is the Basic Commission Bonus (BCB) showing incorrect results when searched by abbreviation?",
                    "How is the total commission calculated, and does it include all necessary components?",
                    "Can you verify the accuracy of Total Commissions, including BCB, SCB, RCB, and PCB?",
                    "Who are the top earners, including all commission components?",
                    "Analyze manager-wise bonus distribution for fair allocation.",
                    "Visualize top earners and their contributions to Gross Earnings.",
                    "Provide insights into Paid As Position trends for bonus distribution.",
                ]
                
                for question in predefined_questions:
                    if st.button(question):
                        response = analyze_chatbot(question, df)
                        st.write(f"**Q: {question}**")
                        st.write(f"**A:** {response}")
                        
                        if "Top Earners" in question:
                            df["Total Commissions"] = df[["Basic commission Bonus(BCB)", "Super Commission Bonus(SCB)", "Recruitment Commission Bonus (RCB)", "Performance Bonus (PCB)"]].sum(axis=1)
                            top_earners = df.nlargest(10, "Total Commissions")[["First Name", "Last Name", "Total Commissions"]]
                            top_earners.insert(0, "Serial Number", range(1, 11))
                            st.write("**Top Earners:**")
                            st.dataframe(top_earners)
                        
                        st.session_state.search_history.append({"question": question, "response": response})
                
                st.subheader("Ask the Chatbot Anything")
                user_question = st.text_input("Enter your question:")
                if st.button("Search"):
                    if user_question:
                        response = analyze_chatbot(user_question, df)
                        st.write(f"**Q: {user_question}**")
                        st.write(f"**A:** {response}")
                        st.session_state.search_history.append({"question": user_question, "response": response})
                    else:
                        st.warning("Please enter a question before searching.")
                
                if st.session_state.search_history:
                    st.subheader("Search History")
                    for entry in st.session_state.search_history:
                        st.write(f"**Q: {entry['question']}**")
                        st.write(f"**A:** {entry['response']}")
        else:
            st.error("Uploaded file is missing required columns.")
