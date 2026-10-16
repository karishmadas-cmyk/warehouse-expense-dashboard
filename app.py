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


def format_inr(val):
    if val >= 1e7:
        return f"₹{val/1e7:.2f} Cr"
    elif val >= 1e5:
        return f"₹{val/1e5:.2f} L"
    elif val >= 1e3:
        return f"₹{val/1e3:.1f} K"
    else:
        return f"₹{val:.0f}"


# Load Data safely
@st.cache_data(show_spinner="Loading Data...")
def load_data():
    df = pd.read_excel("Monthly warehouse expenses.xlsx", header=1)
    df.columns = df.columns.str.strip()
    df["Month_Dt"] = pd.to_datetime(df["Month"])
    df["Month_Str"] = df["Month_Dt"].dt.strftime("%B")
    df["Year"] = df["Month_Dt"].dt.year
    return df


try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading Excel file: {e}")
    st.stop()

# ------------------ APP HEADER ------------------
st.title("Warehouse Operational Expense Dashboard FY 2026-27")
st.markdown("---")

# ------------------ SIDEBAR ------------------
try:
    logo_img = Image.open("Logo.png")
    st.sidebar.image(logo_img, use_container_width=True)
except Exception:
    pass

st.sidebar.header("🔍 Filter Options")

selected_year = st.sidebar.multiselect(
    "Select Year",
    options=sorted(df["Year"].dropna().unique())
)

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

# Dynamic Filtering
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

# ------------------ TOP KPI METRICS ------------------
total_exp = filtered_df["Total Expenses"].sum() if not filtered_df.empty else 0

if selected_month:
    target_budget = sum(MONTHLY_BUDGETS.get(m, 0) for m in selected_month)
else:
    active_months = filtered_df["Month_Str"].unique() if not filtered_df.empty else MONTHLY_BUDGETS.keys()
    target_budget = sum(MONTHLY_BUDGETS.get(m, 0) for m in active_months)

expense_diff = total_exp - target_budget

if expense_diff >
