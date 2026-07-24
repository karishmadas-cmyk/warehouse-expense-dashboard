import pandas as pd
import plotly.express as px
import streamlit as st

# Set Page Title & Layout
st.set_page_config(
    page_title="Warehouse Operational Expense Dashboard FY 2026-27",
    layout="wide",
)


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
    df["Month_Dt"] = pd.to_datetime(df["Month"])
    df["Month_Str"] = df["Month_Dt"].dt.strftime("%B")  # e.g., April, May
    df["Year"] = df["Month_Dt"].dt.year
    return df


df = load_data()

# App Header
st.title("🏭 Warehouse Operational Expense Dashboard FY 2026-27")
st.markdown("---")

# Sidebar Filters & Manual Refresh
st.sidebar.header("🔍 Filter Options")

# Year & Month Filters
selected_year = st.sidebar.multiselect("Select Year", options=sorted(df["Year"].dropna().unique()))

# Filter available month options dynamically based on selected year (if any)
available_months = (
    df[df["Year"].isin(selected_year)]["Month_Str"].unique()
    if selected_year
    else df["Month_Str"].unique()
)
selected_month = st.sidebar.multiselect("Select Month", options=available_months)

st.sidebar.markdown("---")

# Additional Filters
selected_zone = st.sidebar.multiselect("Select Zone", options=df["Zone"].unique())
selected_cust = st.sidebar.multiselect(
    "Select Customer", options=df["Customer"].unique()
)
selected_loc = st.sidebar.multiselect(
    "Select Warehouse Location", options=df["Locations"].unique()
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
    # ------------------ ROW 1: Monthly Trend & Zone ------------------
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
        m_trend["Expense_Cr"] = m_trend["Total Expenses"] / 1e7

        fig1 = px.line(
            m_trend,
            x="Month_Str",
            y="Expense_Cr",
            markers=True,
            text=m_trend["Total Expenses"].apply(format_inr),
        )
        fig1.update_xaxes(type="category", title_text="")
        fig1.update_yaxes(title_text="Expense (₹ Cr)", ticksuffix=" Cr")
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

    # ------------------ ROW 2: Categories & Customers ------------------
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
        cat_sum["Expense_Cr"] = cat_sum["Expense"] / 1e7

        fig3 = px.bar(
            cat_sum,
            x="Expense_Cr",
            y="Category",
            orientation="h",
            color_discrete_sequence=["#0078D4"],
            text=cat_sum["Expense"].apply(lambda x: f" {format_inr(x)}"),
        )
        fig3.update_xaxes(title_text="Expense (₹ Cr)", ticksuffix=" Cr")
        fig3.update_traces(textposition="outside")
        fig3.update_layout(
            height=380, yaxis_title="", margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("👥 Top Customers by Expense")
        cust_sum = (
            filtered_df.groupby("Customer")["Total Expenses"]
            .sum()
            .reset_index()
            .sort_values("Total Expenses", ascending=True)
            .tail(7)
        )
        cust_sum["Expense_Cr"] = cust_sum["Total Expenses"] / 1e7

        fig4 = px.bar(
            cust_sum,
            x="Expense_Cr",
            y="Customer",
            orientation="h",
            color_discrete_sequence=["#6B2D5C"],
            text=cust_sum["Total Expenses"].apply(lambda x: f" {format_inr(x)}"),
        )
        fig4.update_xaxes(title_text="Expense (₹ Cr)", ticksuffix=" Cr")
        fig4.update_traces(textposition="outside")
        fig4.update_layout(
            height=380, yaxis_title="", margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")

    # ------------------ ROW 3: Warehouses & Detail Table ------------------
    col5, col6 = st.columns([1, 1])

    with col5:
        st.subheader("🏬 Top Warehouses by Expense")
        loc_sum = (
            filtered_df.groupby("Locations")["Total Expenses"]
            .sum()
            .reset_index()
            .sort_values("Total Expenses", ascending=True)
            .tail(7)
        )
        loc_sum["Expense_Cr"] = loc_sum["Total Expenses"] / 1e7

        fig5 = px.bar(
            loc_sum,
            x="Expense_Cr",
            y="Locations",
            orientation="h",
            color_discrete_sequence=["#2B579A"],
            text=loc_sum["Total Expenses"].apply(lambda x: f" {format_inr(x)}"),
        )
        fig5.update_xaxes(title_text="Expense (₹ Cr)", ticksuffix=" Cr")
        fig5.update_traces(textposition="outside")
        fig5.update_layout(
            height=380, yaxis_title="", margin=dict(l=20, r=20, t=30, b=20)
        )
        st.plotly_chart(fig5, use_container_width=True)

    with col6:
        st.subheader("📋 EXPENSE DETAIL SUMMARY")
        detail_df = (
            filtered_df.groupby(["Customer", "Locations", "Year", "Month_Str"])[
                "Total Expenses"
            ]
            .sum()
            .reset_index()
            .sort_values(by="Total Expenses", ascending=False)
        )
        detail_df.columns = [
            "Customer",
            "Locations",
            "Year",
            "Month",
            "Total Expense",
        ]

        formatted_detail_df = detail_df.copy()
        formatted_detail_df["Total Expense"] = formatted_detail_df[
            "Total Expense"
        ].apply(lambda x: f"₹ {x:,.0f}")

        st.dataframe(formatted_detail_df, use_container_width=True, height=310)

    # Detailed Full Dataset View
    with st.expander("📄 View Full Line-Item Data Table"):
        st.dataframe(filtered_df, use_container_width=True)
