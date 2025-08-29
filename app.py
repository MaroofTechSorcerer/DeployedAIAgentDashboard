import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import spacy
import json

# --- This section is changed to get the secret key from Streamlit's secure vault ---
try:
    # Get the Google credentials from the secret vault
    creds_json_str = st.secrets["gcp_service_account"]
    creds_dict = json.loads(creds_json_str)
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
    )
# If the secret is not found, show an error and stop.
except (KeyError, json.JSONDecodeError):
    st.error("Google Sheets credentials are not set up correctly. Please add them to your Streamlit secrets.")
    st.stop()

# --- Everything below this line is your original code. No features were changed. ---

def get_google_sheet(spreadsheet_id, range_name):
    try:
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        
        if not values:
            st.error('No data found.')
            return None

        df = pd.DataFrame(values[1:], columns=values[0])
        return df

    except Exception as e:
        st.error(f'Error connecting to Google Sheets: {e}')
        return None

def extract_info(df, column, prompt):
    try:
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(prompt)
        prompt = prompt.lower()
        if "minimum" in prompt or "lowest" in prompt:
            result = df[column].astype(float).min()
            return f"The minimum value in column '{column}' is {result}."
        elif "maximum" in prompt or "highest" in prompt:
            result = df[column].astype(float).max()
            return f"The maximum value in column '{column}' is {result}."
        elif "average" in prompt or "mean" in prompt:
            result = df[column].astype(float).mean()
            return f"The average value in column '{column}' is {result}."
        elif "sum" in prompt or "total" in prompt:
            result = df[column].astype(float).sum()
            return f"The sum of values in column '{column}' is {result}."
        elif "count" in prompt or "number of" in prompt:
            result = df[column].count()
            return f"The count of values in column '{column}' is {result}."
        elif "median" in prompt:
            result = df[column].astype(float).median()
            return f"The median value in column '{column}' is {result}."
        elif "standard deviation" in prompt or "std dev" in prompt:
            result = df[column].astype(float).std()
            return f"The standard deviation of values in column '{column}' is {result}."
        elif "variance" in prompt:
            result = df[column].astype(float).var()
            return f"The variance of values in column '{column}' is {result}."
        else:
            return "Query not supported. Please rephrase your query to include 'minimum', 'maximum', 'average', 'sum', 'count', 'median', 'standard deviation', or 'variance'."
    except Exception as e:
        return f"Error: {e}"

def main():
    st.title("AI Agent Dashboard")
    st.write("This dashboard allows you to upload CSV files or connect to Google Sheets, and extract information using natural language queries.")
    
    # File uploading section
    st.header("Upload CSV")
    uploaded_file = st.file_uploader("Upload CSV", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.write("Uploaded Data Preview:")
        st.write(df.head())
        if not df.empty:
            columns = df.columns.tolist()
            selected_column = st.selectbox("Select the column with numeric values", columns, key='csv_col_select')
            query = st.text_input("Enter your custom prompt (e.g., 'Get me the minimum value of column X'):", key='csv_query')
            if st.button("Extract Information", key='csv_extract'):
                extracted_info = extract_info(df, selected_column, query)
                st.write({"Extracted Info": extracted_info})
                
                result_df = pd.DataFrame([{"Extracted Info": extracted_info}])
                csv = result_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Extracted Information",
                    data=csv,
                    file_name="extracted_info.csv",
                    mime="text/csv"
                )

    # Google Sheets connection section
    st.header("Connect to Google Sheets")
    spreadsheet_id = st.text_input("Enter Google Sheets ID")
    range_name = st.text_input("Enter data range (e.g., Sheet1!A1:D10)")

    if st.button("Load Google Sheet"):
        if spreadsheet_id and range_name:
            df = get_google_sheet(spreadsheet_id, range_name)
            if df is not None:
                st.session_state['google_df'] = df
                st.write("Google Sheet Data Preview:")
                st.write(df.head())
            else:
                st.error("No data found. Please check the Google Sheets ID and range.")
        else:
            st.error("Please provide both Google Sheets ID and range.")

    if 'google_df' in st.session_state:
        df = st.session_state['google_df']
        columns = df.columns.tolist()
        selected_column = st.selectbox("Select the column with numeric values", columns, key='google_col_select')
        query = st.text_input("Enter your custom prompt (e.g., 'Get me the minimum value of column X'):", key='google_query')
        if st.button("Extract Information from Google Sheet", key='google_extract'):
            extracted_info = extract_info(df, selected_column, query)
            st.write({"Extracted Info": extracted_info})
            
            result_df = pd.DataFrame([{"Extracted Info": extracted_info}])
            csv = result_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Extracted Information",
                data=csv,
                file_name="extracted_info.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()