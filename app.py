import pandas as pd
import plotly.express as px
import streamlit as st

# Set Page Title & Layout
st.set_page_config(
    page_title="Warehouse Operational Expense Dashboard FY 2026-27",
    layout="wide",
)


# Helper function for Indian Numbering System
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
    df["Month_Dt"] = pd.to_datetime(df["Month"])
    df["Month_Str"] = df["Month_Dt"].dt.strftime("%b %Y")
    return df


df = load_data()

# App Header
st.title("🏭 Warehouse Operational Expense Dashboard FY 2026-27")
st.markdown("---")

# Sidebar Filters
st.sidebar.header("🔍 Filter Options")
selected_zone = st.sidebar.multiselect("Select Zone", options=df["Zone"].unique())
selected_cust = st.sidebar.multiselect(
    "Select Customer", options=df["Customer"].unique()
)
selected_loc = st.sidebar.multiselect(
    "Select Warehouse Location", options=df["Locations"].unique()
)

# Dynamic Filter Logic
filtered_df = df.copy()

if selected_zone:
    filtered_df = filtered_df[filtered_df["Zone"].isin(selected_zone)]

if selected_cust:
    filtered_df = filtered_df[filtered_df["Customer"].isin(selected_cust)]

if selected_loc:
    filtered_df = filtered_df[filtered_df["Locations"].isin(selected_loc)]

# Top KPI Metric Cards
total_exp = filtered_df["Total Expenses"].sum() if not filtered_df.empty else 0
avg_exp = filtered_df["Total Expenses"].mean() if not filtered_df.empty else 0

col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
col_kpi1.metric("Total Expense", format_inr(total_exp))
col_kpi2.metric("Total Warehouses", filtered_df["Locations"].nunique())
col_kpi3.metric("Total Customers", filtered_df["Customer"].nunique())
col_kpi4.metric("Avg Expense / Line Item", format_inr(avg_exp))

st.markdown("---")

if filtered_df.empty:
    st.warning("⚠️ No data available for the selected combination of filters.")
else:
    # ------------------ ROW 1: 2-COLUMN GRID ------------------
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.subheader("📈 Monthly Expense Trend")
        m_trend = (
            filtered_df.groupby(["Month_Dt", "Month_Str"])["Total Expenses"]
            .sum()
            .reset_index()
            .sort_values("Month_Dt")
        )
        m_trend = m_trend[m_trend["Total Expenses"] > 0]

        fig1 = px.line(
            m_trend,
            x="Month_Str",
            y="Total Expenses",
            markers=True,
            text=m_trend["Total Expenses"].apply(format_inr),
        )
        fig1.update_xaxes(type="category", title_text="")
        fig1.update_yaxes(title_text="Total Expense")
        fig1.update_traces(
            textposition="top center", line=dict(width=3, color="#0078D4")
        )
        fig1.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("🌍 Expense Distribution by Zone")
        z_sum = (
            filtered_df.groupby("Zone")["Total Expenses"].sum().reset_index()
        )
        fig2 = px.pie(
            z_sum,
            values="Total Expenses",
            names="Zone",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig2.update_traces(textinfo="percent+label")
        fig2.update_layout(
            height=350, showlegend=False, margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # ------------------ ROW 2: 2-COLUMN GRID ------------------
    col3, col4 = st.columns([1, 1])

    with col3:
        st.subheader("📊 Top Expense Categories")
        cat_cols = [
            "Manpower Outsource",
            "Security Outsource",
            "VAS MP",
            "Electricity",
            "Tea",
            "Water",
            "Printing & Stationery",
            "Petty Cash",
            "DG",
            "Rental Printer",
            "Internet expenses",
            "Pest Control",
            "Other expenses",
        ]
        cat_sum = filtered_df[cat_cols].sum().reset_index()
        cat_sum.columns = ["Category", "Expense"]

        cat_sum = cat_sum[cat_sum["Expense"] > 0].sort_values(
            "Expense", ascending=True
        )

        fig3 = px.bar(
            cat_sum,
            x="Expense",
            y="Category",
            orientation="h",
            color_discrete_sequence=["#0078D4"],
            text=cat_sum["Expense"].apply(lambda x: f" {format_inr(x)}"),
        )
        fig3.update_traces(textposition="outside")
        fig3.update_layout(
            height=400,
            xaxis_title="",
            yaxis_title="",
            margin=dict(l=20, r=20, t=30, b=20),
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("🏬 Top Warehouses by Expense")
        loc_sum = (
            filtered_df.groupby("Locations")["Total Expenses"]
            .sum()
            .reset_index()
            .sort_values("Total Expenses", ascending=True)
            .tail(7)
        )

        fig4 = px.bar(
            loc_sum,
            x="Total Expenses",
            y="Locations",
            orientation="h",
            color_discrete_sequence=["#2B579A"],
            text=loc_sum["Total Expenses"].apply(lambda x: f" {format_inr(x)}"),
        )
        fig4.update_traces(textposition="outside")
        fig4.update_layout(
            height=400,
            xaxis_title="",
            yaxis_title="",
            margin=dict(l=20, r=20, t=30, b=20),
        )
        st.plotly_chart(fig4, use_container_width=True)

    # Raw Data View
    with st.expander("📄 View Detailed Table"):
        st.dataframe(filtered_df, use_container_width=True)
