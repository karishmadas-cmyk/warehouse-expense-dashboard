import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

# Set Page Title & Layout
st.set_page_config(
    page_title="Warehouse Operational Expense Dashboard FY 2026-27",
    layout="wide",
)

# -----------------------------------------------------------------------------
# MONTHLY BUDGET CONFIGURATION (In INR)
# Note: Values use e7 notation (e.g., 7.14e7 = ₹7.14 Cr)
# -----------------------------------------------------------------------------
MONTHLY_BUDGETS = {
    "April": 7.14e7,      # ₹7.14 Cr
    "May": 6.84e7,        # ₹6.84 Cr
    "June": 7.13e7,       # ₹7.13 Cr
    "July": 7.48e7,       # ₹7.48 Cr
    "August": 7.45e7,     # ₹7.45 Cr
    "September": 7.48e7,  # ₹7.48 Cr
    "October": 7.98e7,    # ₹7.98 Cr
    "November": 7.89e7,   # ₹7.89 Cr
    "December": 8.48e7,   # ₹8.48 Cr
    "January": 8.73e7,    # ₹8.73 Cr
    "February": 8.82e7,   # ₹8.82 Cr
    "March": 9.68e7       # ₹9.68 Cr
}


# Helper function for Indian Currency Formatting
def format_inr(val):
    if val >= 1e7:
        return f"₹{val/1e7:.2f} Cr"
    elif val >= 1e5:
        return f"₹{val/1e5:.2f} L"
    elif val >= 1e3:
        return f"₹{val/1e3:.1f} K"
    else:
        return f"₹{val:.0f}"


# Load Data
@st.cache_data
def load_data():
    df = pd.read_excel("Monthly warehouse expenses.xlsx", header=1)
    df.columns = df.columns.str.strip()  # Clean whitespace from column names
    df["Month_Dt"] = pd.to_datetime(df["Month"])
    df["Month_Str"] = df["Month_Dt"].dt.strftime("%B")  # e.g., April, May
    df["Year"] = df["Month_Dt"].dt.year
    return df


df = load_data()

# ------------------ APP HEADER (CLEAN MAIN TITLE) ------------------
st.title("Warehouse Operational Expense Dashboard FY 2026-27")
st.markdown("---")

# ------------------ SIDEBAR WITH LOGO AT TOP ------------------
try:
    logo_img = Image.open("Logo.png")
    st.sidebar.image(logo_img, use_container_width=True)
except Exception:
    pass

st.sidebar.header("🔍 Filter Options")

# Year & Month Filters
selected_year = st.sidebar.multiselect(
    "Select Year",
    options=sorted(df["Year"].dropna().unique())
)

# Filter available month options dynamically based on selected year
available_months = (
    df[df["Year"].isin(selected_year)]["Month_Str"].unique()
    if selected_year
    else df["Month_Str"].unique()
)

selected_month = st.sidebar.multiselect(
    "Select Month",
    options=available_months
)

st.sidebar.markdown("---")

# Additional Filters
selected_zone = st.sidebar.multiselect(
    "Select Zone",
    options=df["Zone"].dropna().unique()
)

selected_cust = st.sidebar.multiselect(
    "Select Customer",
    options=df["Customer"].dropna().unique()
)

selected_loc = st.sidebar.multiselect(
    "Select Warehouse Location",
    options=df["Locations"].dropna().unique()
)

st.sidebar.markdown("---")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Dynamic Filter Logic
filtered_df = df.copy()

if selected_year:
    filtered_df = filtered_df[filtered_df["Year"].isin(selected_year)]

if selected_month:
    filtered_df = filtered_df[filtered_df["Month_Str"].isin(selected_month)]

if selected_zone:
    filtered_df = filtered_df[filtered_df["Zone"].isin(selected_zone)]

if selected_cust:
    filtered_df = filtered_df[filtered_df["Customer"].isin(selected_cust)]

if selected_loc:
    filtered_df = filtered_df[filtered_df["Locations"].isin(selected_loc)]

# ------------------ TOP KPI METRIC CAR
