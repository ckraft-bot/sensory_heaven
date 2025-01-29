import os
import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Load service account credentials
SERVICE_ACCOUNT_FILE = r"credentials.json"  # Update with your JSON file
SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

def get_google_api_usage():
    """Fetch API usage data from Google Cloud."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    
    service = build("serviceusage", "v1", credentials=credentials)
    project_name = f"projects/your-project-id"  # Update with your project ID

    try:
        response = service.services().list(parent=project_name).execute()
        api_usage = response.get("services", [])
        return api_usage
    except Exception as e:
        st.error(f"Error fetching API usage: {e}")
        return None

def get_billing_data():
    """Fetch billing costs from Google Cloud Billing API."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )

    service = build("cloudbilling", "v1", credentials=credentials)
    billing_account_id = "your-billing-account-id"  # Update this with your billing account ID

    try:
        response = service.billingAccounts().reports().generate(
            name=f"billingAccounts/{billing_account_id}"
        ).execute()
        
        # Parse response to extract cost data
        cost_data = []
        for entry in response.get("reports", []):
            service_name = entry.get("service", "Unknown Service")
            cost = entry.get("cost", {}).get("amount", 0.0)
            cost_data.append({"Service": service_name, "Cost": cost})
        
        return pd.DataFrame(cost_data)

    except Exception as e:
        st.error(f"Error fetching billing data: {e}")
        return None

def display_api_usage():
    """Render API usage data in Streamlit."""
    st.title("Google API Usage & Costs")

    usage_data = get_google_api_usage()
    billing_data = get_billing_data()
    
    if usage_data:
        api_info = []
        for service in usage_data:
            api_name = service.get("config", {}).get("name", "Unknown API")
            enabled_status = service.get("state", "Unknown")
            api_info.append({"API Name": api_name, "Status": enabled_status})

        api_df = pd.DataFrame(api_info)
        st.subheader("API Usage Summary")
        st.dataframe(api_df)

    if billing_data is not None:
        st.subheader("Estimated API Costs")
        st.dataframe(billing_data)

if __name__ == "__main__":
    display_api_usage()
