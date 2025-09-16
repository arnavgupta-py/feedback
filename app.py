# D:\arnav\app.py

import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
import plotly.express as px

# --- APP CONFIGURATION ---
WORKSHEET_NAME = "product_vidya"

st.set_page_config(
    page_title="Event Feedback Dashboard",
    page_icon="✨",
    layout="wide"
)

# --- STYLING AND ANIMATIONS ---
st.markdown("""
<style>
    /* --- Main App Styling --- */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
    body { font-family: 'Poppins', sans-serif; }
    .stApp {
        background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    /* --- Form Styling (Glassmorphism) --- */
    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem 3rem;
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        animation: fadeInUp 0.5s ease-in-out;
    }
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    /* --- Widget Styling --- */
    h1, h2, h3, h4, h5, h6, p, label { color: #FFFFFF !important; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] > div {
        background-color: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #FFFFFF;
        border-radius: 10px;
    }
    /* Custom Radio Buttons */
    div[data-testid="stRadio"] > label {
        display: inline-flex;
        background: rgba(255, 255, 255, 0.1);
        padding: 10px 15px;
        margin: 5px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
        cursor: pointer;
    }
    div[data-testid="stRadio"] > label:hover {
        background: rgba(255, 255, 255, 0.3);
        transform: scale(1.05);
    }
    div[data-testid="stRadio"] input { display: none; }
    /* --- Submit Button Animation --- */
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(45deg, #FF4B2B, #FF416C);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        transition: all 0.3s ease-in-out;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stFormSubmitButton"] button:active { transform: translateY(0); }
    /* --- Analytics Section --- */
    div[data-testid="stPlotlyChart"] {
        border-radius: 15px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS CONNECTION ---
def get_google_sheet_client():
    try:
        creds_json = st.secrets["gsheets"]["service_account"]
        client = gspread.service_account_from_dict(creds_json)
        return client
    except KeyError:
        st.error("Google Sheets service account credentials not found in secrets.")
        st.stop()
    except Exception as e:
        st.error(f"Failed to create Google Sheets client: {e}")
        st.stop()

@st.cache_resource(ttl=300)
def get_spreadsheet(_client):
    try:
        sheet_url = st.secrets["gsheets"]["url"]
        spreadsheet = _client.open_by_url(sheet_url)
        return spreadsheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("Spreadsheet not found. Please check the URL in your secrets file.")
        st.stop()
    except Exception as e:
        st.error(f"Could not open spreadsheet: {e}")
        st.stop()

# --- DATA FETCHING AND MANIPULATION ---
@st.cache_data(ttl=300)
def fetch_data():
    try:
        client = get_google_sheet_client()
        spreadsheet = get_spreadsheet(client)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        data = worksheet.get_all_records()
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df.columns = [str(col).strip().lower() for col in df.columns]
        return df
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Worksheet named '{WORKSHEET_NAME}' not found in the spreadsheet.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An error occurred while fetching data: {e}")
        return pd.DataFrame()

def append_row_to_sheet(new_data):
    try:
        client = get_google_sheet_client()
        spreadsheet = get_spreadsheet(client)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        header = [str(h).strip().lower() for h in worksheet.row_values(1)]
        row_to_append = [new_data.get(col, None) for col in header]
        worksheet.append_row(row_to_append)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error submitting feedback: {e}")
        return False

# --- UI SETUP ---
st.title("Event Feedback Form")
st.markdown("Your feedback is vital to us. Please take a moment to share your experience.")

# --- TAB LAYOUT ---
feedback_tab, analytics_tab = st.tabs(["✍️ Feedback", "📊 Analytics"])

# --- FEEDBACK TAB ---
with feedback_tab:
    with st.form(key="feedback_form"):
        st.header("Your Details")
        name = st.text_input("Name:", help="Please enter your full name.")
        
        col1, col2 = st.columns(2)
        with col1:
            department_options = ["COMPS", "CSE(DS)", "AIDS", "IT", "EXTC", "VLSI", "MECH", "CIVIL", "Others"]
            department = st.selectbox("Department:", department_options)
        with col2:
            year = st.selectbox("Year:", ["First Year", "Second Year", "Third Year", "Fourth Year"])

        st.header("Event Rating")
        st.markdown("Please rate the following on a scale of 1 to 5.")

        rating_emojis = ["😡", "🙁", "😐", "🙂", "😀"]
        emoji_to_rating = {"😡": 1, "🙁": 2, "😐": 3, "🙂": 4, "😀": 5}
        
        q_content = st.radio("Content of the sessions:", options=rating_emojis, index=2, horizontal=True)
        q_relevance = st.radio("Relevance of the topics:", options=rating_emojis, index=2, horizontal=True)
        q_speakers = st.radio("Quality of the speakers:", options=rating_emojis, index=2, horizontal=True)
        q_organization = st.radio("Organization of the event:", options=rating_emojis, index=2, horizontal=True)
        q_overall = st.radio("Overall experience:", options=rating_emojis, index=2, horizontal=True)

        submit_button = st.form_submit_button("Submit Feedback")

        if submit_button:
            new_data = {
                "serial": len(fetch_data()) + 1,
                "time_stamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "name": name,
                "department": department,
                "year": year,
                "question_1": emoji_to_rating.get(q_content),
                "question_2": emoji_to_rating.get(q_relevance),
                "question_3": emoji_to_rating.get(q_speakers),
                "question_4": emoji_to_rating.get(q_organization),
                "question_5": emoji_to_rating.get(q_overall)
            }
            
            if append_row_to_sheet(new_data):
                st.success("Thank you for your feedback! Your response has been recorded.")
                st.balloons()

# --- ANALYTICS TAB ---
with analytics_tab:
    st.header("Live Event Feedback Analytics")
    df_data = fetch_data()

    if not df_data.empty:
        st.subheader(f"Total Responses: {len(df_data)}")
        if 'department' in df_data.columns:
            department_counts = df_data['department'].value_counts().reset_index()
            department_counts.columns = ['Department', 'Number of Respondents']
            fig_bar_dept = px.bar(
                department_counts, x='Department', y='Number of Respondents',
                title='Distribution of Respondents by Department', text_auto=True
            )
            
            # Style the department chart
            fig_bar_dept.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(255,255,255,0.1)',
                font_color='white',
                title_x=0.5,
                yaxis=dict(gridcolor='rgba(255,255,255,0.2)')
            )

            st.plotly_chart(fig_bar_dept, use_container_width=True)

        rating_cols = ['question_1', 'question_2', 'question_3', 'question_4', 'question_5']
        existing_rating_cols = [col for col in rating_cols if col in df_data.columns]
        
        if existing_rating_cols:
            for col in existing_rating_cols:
                df_data[col] = pd.to_numeric(df_data[col], errors='coerce')
            ratings_df = df_data.dropna(subset=existing_rating_cols)
            if not ratings_df.empty:
                avg_ratings = ratings_df[existing_rating_cols].mean().reset_index()
                avg_ratings.columns = ['Question', 'Average Rating']
                question_labels = {
                    'question_1': 'Content', 'question_2': 'Relevance',
                    'question_3': 'Speakers', 'question_4': 'Organization',
                    'question_5': 'Overall'
                }
                avg_ratings['Question'] = avg_ratings['Question'].map(question_labels)
                fig_bar_ratings = px.bar(
                    avg_ratings, x='Question', y='Average Rating',
                    title='Average Ratings by Aspect',
                    text=avg_ratings['Average Rating'].apply(lambda x: f'{x:.2f}'),
                    range_y=[1, 5]
                )
                fig_bar_ratings.update_traces(textposition='outside')

                # Style the ratings chart
                fig_bar_ratings.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(255,255,255,0.1)',
                    font_color='white',
                    title_x=0.5,
                    yaxis=dict(gridcolor='rgba(255,255,255,0.2)')
                )

                st.plotly_chart(fig_bar_ratings, use_container_width=True)
            else:
                st.warning("No valid rating data is available to display analytics.")
        else:
            st.warning("Rating columns (e.g., 'question_1') not found in the sheet.")
    else:
        st.info("No feedback data has been submitted yet. Be the first to respond!")