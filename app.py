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
    "April": 7.14e7,
    "May": 6.84e7,
    "June": 7.13e7,
    "July": 7.48e7,
    "August": 7.45e7,
    "September": 7.48e7,
    "October": 7.98e7,
    "November": 7.89e7,
    "December": 8.48e7,
    "January": 8.73e7,
    "February": 8.82e7,
    "March": 9.68e7,
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


def format_sqft(val):
    return f"{val:,.0f} Sq. Ft."


# ------------------ LOAD DATA ------------------
@st.cache_data
def load_data():
    file_path = "Monthly warehouse expenses_3.xlsx"

    # 1. LOAD MAIN EXPENSE SHEET (Client-wise Utilised & Additional Space)
    df_raw = pd.read_excel(file_path, sheet_name=0, header=None)

    # Locate main header row dynamically
    header_idx = 0
    for idx, row in df_raw.iterrows():
        row_str = row.astype(str).str.upper().tolist()
        if any("MONTH" in x or "CUSTOMER" in x for x in row_str):
            header_idx = idx
            break

    df_exp = pd.read_excel(file_path, sheet_name=0, header=header_idx)
    df_exp.columns = df_exp.columns.astype(str).str.strip()

    df_exp["Month_Dt"] = pd.to_datetime(df_exp["Month"])
    df_exp["Month_Str"] = df_exp["Month_Dt"].dt.strftime("%B")
    df_exp["Year"] = df_exp["Month_Dt"].dt.year

    # Map Space Columns in Main Sheet
    for col in df_exp.columns:
        c_upper = col.upper()
        if "UTILISED" in c_upper or "UTILIZED" in c_upper:
            df_exp.rename(columns={col: "Utilised_Space"}, inplace=True)
        elif "ADDITIONAL" in c_upper:
            df_exp.rename(columns={col: "Additional_Space"}, inplace=True)

    # Convert numeric
    for col in ["Utilised_Space", "Additional_Space"]:
        if col in df_exp.columns:
            df_exp[col] = pd.to_numeric(df_exp[col], errors="coerce").fillna(0)
        else:
            df_exp[col] = 0

    # 2. LOAD LOCATION SHEET (Warehouse Total Space)
    df_loc = pd.read_excel(file_path, sheet_name="Location")
    df_loc.columns = df_loc.columns.astype(str).str.strip()
    df_loc["Month_Dt"] = pd.to_datetime(df_loc["Month"])
    df_loc["Month_Str"] = df_loc["Month_Dt"].dt.strftime("%B")
    df_loc["Year"] = df_loc["Month_Dt"].dt.year

    # Map Total Space column
    for col in df_loc.columns:
        if "TOTAL SPACE" in col.upper():
            df_loc.rename(columns={col: "Total_Space"}, inplace=True)

    df_loc["Total_Space"] = pd.to_numeric(df_loc["Total_Space"], errors="coerce").fillna(0)

    return df_exp, df_loc


df, df_loc = load_data()

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
    "Select Year", options=sorted(df["Year"].dropna().unique())
)

available_months = (
    df[df["Year"].isin(selected_year)]["Month_Str"].unique()
    if selected_year
    else df["Month_Str"].unique()
)

selected_month = st.sidebar.multiselect(
    "Select Month", options=available_months
)

st.sidebar.markdown("---")

selected_zone = st.sidebar.multiselect(
    "Select Zone", options=df["Zone"].unique() if "Zone" in df.columns else []
)

selected_cust = st.sidebar.multiselect(
    "Select Customer", options=df["Customer"].unique() if "Customer" in df.columns else []
)

selected_loc = st.sidebar.multiselect(
    "Select Warehouse Location", options=df["Locations"].unique() if "Locations" in df.columns else []
)

st.sidebar.markdown("---")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Dynamic Filtering Logic
filtered_df = df.copy()
filtered_loc = df_loc.copy()

if selected_year:
    filtered_df = filtered_df[filtered_df["Year"].isin(selected_year)]
    filtered_loc = filtered_loc[filtered_loc["Year"].isin(selected_year)]

if selected_month:
    filtered_df = filtered_df[filtered_df["Month_Str"].isin(selected_month)]
    filtered_loc = filtered_loc[filtered_loc["Month_Str"].isin(selected_month)]

if selected_zone:
    if "Zone" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Zone"].isin(selected_zone)]
    if "Zone" in filtered_loc.columns:
        filtered_loc = filtered_loc[filtered_loc["Zone"].isin(selected_zone)]

if selected_cust and "Customer" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Customer"].isin(selected_cust)]

if selected_loc:
    if "Locations" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["Locations"].isin(selected_loc)]
    if "Locations" in filtered_loc.columns:
        filtered_loc = filtered_loc[filtered_loc["Locations"].isin(selected_loc)]


# ------------------ SPACE CALCULATIONS ------------------
# Total space is pulled from Location sheet
total_space_sqft = filtered_loc["Total_Space"].sum()

# Utilised & Additional space are pulled from main Expense sheet
utilised_space_sqft = filtered_df["Utilised_Space"].sum()
additional_space_sqft = filtered_df["Additional_Space"].sum()


# ------------------ TOP KPI METRIC CARDS ------------------
total_exp = (
    filtered_df["Total Expenses"].sum()
    if not filtered_df.empty and "Total Expenses" in filtered_df.columns
    else 0
)

if selected_month:
    target_budget = sum(MONTHLY_BUDGETS.get(m, 0) for m in selected_month)
else:
    active_months = (
        filtered_df["Month_Str"].unique()
        if not filtered_df.empty
        else MONTHLY_BUDGETS.keys()
    )
    target_budget = sum(MONTHLY_BUDGETS.get(m, 0) for m in active_months)

expense_diff = total_exp - target_budget

if expense_diff > 0:
    delta_text = f"▲ {format_inr(abs(expense_diff))} Above Budget"
    delta_color_style = "#d9383a"
else:
    delta_text = f"▼ {format_inr(abs(expense_diff))} Below Budget"
    delta_color_style = "#28a745"

# Row 1 KPIs
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

with col_kpi1:
    st.markdown(
        f"""
        <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px 15px;">
            <span style="font-size: 14px; color: #555555;">Total Expense</span>
            <div style="font-size: 28px; font-weight: bold; color: #1f1f1f; margin-top: 2px;">
                {format_inr(total_exp)}
            </div>
            <div style="font-size: 13px; font-weight: 600; color: {delta_color_style}; margin-top: 4px;">
                {delta_text}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_kpi2:
    st.metric(
        "Total Warehouses",
        filtered_loc["Locations"].nunique()
        if not filtered_loc.empty and "Locations" in filtered_loc.columns
        else 0,
    )

with col_kpi3:
    st.metric(
        "Total Customers",
        filtered_df["Customer"].nunique()
        if not filtered_df.empty and "Customer" in filtered_df.columns
        else 0,
    )

st.markdown("<br>", unsafe_allow_html=True)

# Row 2 Space Analytics KPIs
col_sp1, col_sp2, col_sp3 = st.columns(3)

with col_sp1:
    st.metric("📦 Total Space (Location Sheet)", format_sqft(total_space_sqft))

with col_sp2:
    st.metric("🏢 Utilised Space", format_sqft(utilised_space_sqft))

with col_sp3:
    st.metric("➕ Additional Space Used", format_sqft(additional_space_sqft))

st.markdown("---")

# ------------------ SPACE BREAKDOWN CHART ------------------
if not filtered_df.empty:
    st.subheader("📐 Monthwise Space Utilization Breakdown")

    # Aggregate Total Space per month from Location sheet
    m_loc = (
        filtered_loc.groupby(["Month_Dt", "Month_Str"])["Total_Space"]
        .sum()
        .reset_index()
    )

    # Aggregate Utilised and Additional Space per month from Main sheet
    m_exp = (
        filtered_df.groupby(["Month_Dt", "Month_Str"])[
            ["Utilised_Space", "Additional_Space"]
        ]
        .sum()
        .reset_index()
    )

    m_space_df = pd.merge(
        m_loc, m_exp, on=["Month_Dt", "Month_Str"], how="outer"
    ).fillna(0).sort_values("Month_Dt")

    fig_space = go.Figure()
    fig_space.add_trace(
        go.Bar(
            x=m_space_df["Month_Str"],
            y=m_space_df["Total_Space"],
            name="Total Warehouse Space",
            marker_color="#2B579A",
        )
    )
    fig_space.add_trace(
        go.Bar(
            x=m_space_df["Month_Str"],
            y=m_space_df["Utilised_Space"],
            name="Utilised Space",
            marker_color="#0078D4",
        )
    )
    fig_space.add_trace(
        go.Bar(
            x=m_space_df["Month_Str"],
            y=m_space_df["Additional_Space"],
            name="Additional Space Used",
            marker_color="#6B2D5C",
        )
    )

    fig_space.update_layout(
        barmode="group",
        height=360,
        title="Total vs. Utilised vs. Additional Space (Sq. Ft.)",
        margin=dict(l=20, r=20, t=40, b=20),
        yaxis_title="Area (Sq. Ft.)",
    )
    st.plotly_chart(fig_space, use_container_width=True)
