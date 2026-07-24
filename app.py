import pandas as pd
import plotly.express as px
import streamlit as st

# Set Page Title & Layout
st.set_page_config(
    page_title="Warehouse Operational Expense Dashboard FY 2026-27",
    layout="wide",
)


# Load Data
@st.cache_data
def load_data():
    df = pd.read_excel("Monthly warehouse expenses.xlsx", header=1)
    df["Month_Str"] = pd.to_datetime(df["Month"]).dt.strftime("%b %Y")
    return df


df = load_data()

# App Header
st.title("🏭 WAREHOUSE OPERATIONAL EXPENSE DASHBOARD FY 2026-27")
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

# --- Dynamic Filter Logic ---
# If a filter is left empty, it includes ALL options by default
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

col_kpi1.metric("Total Expense", f"₹ {total_exp / 1e7:.2f} Cr")
col_kpi2.metric("Total Warehouses", filtered_df["Locations"].nunique())
col_kpi3.metric("Total Customers", filtered_df["Customer"].nunique())
col_kpi4.metric("Avg Expense / Line Item", f"₹ {avg_exp / 1e5:.2f} L")

st.markdown("---")

# If no data matches the selected filters, show a friendly warning
if filtered_df.empty:
    st.warning("⚠️ No data available for the selected combination of filters.")
else:
    # Visualizations - Row 1
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Monthly Trend")
        m_trend = (
            filtered_df.groupby("Month_Str")["Total Expenses"]
            .sum()
            .reset_index()
        )
        fig1 = px.line(
            m_trend,
            x="Month_Str",
            y="Total Expenses",
            markers=True,
            text=m_trend["Total Expenses"].apply(lambda x: f"₹{x/1e6:.1f}M"),
        )
        fig1.update_traces(textposition="top center")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Expense by Category")
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
        fig2 = px.bar(
            cat_sum.sort_values("Expense", ascending=True),
            x="Expense",
            y="Category",
            orientation="h",
            color="Expense",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        st.subheader("Expense by Zone")
        z_sum = (
            filtered_df.groupby("Zone")["Total Expenses"].sum().reset_index()
        )
        fig3 = px.pie(z_sum, values="Total Expenses", names="Zone", hole=0.45)
        st.plotly_chart(fig3, use_container_width=True)

    # Visualizations - Row 2
    col4, col5 = st.columns(2)

    with col4:
        st.subheader("Top Customers by Expense")
        cust_sum = (
            filtered_df.groupby("Customer")["Total Expenses"]
            .sum()
            .reset_index()
            .sort_values("Total Expenses", ascending=False)
            .head(7)
        )
        fig4 = px.bar(
            cust_sum,
            x="Total Expenses",
            y="Customer",
            orientation="h",
            color="Total Expenses",
            color_continuous_scale="Purples",
        )
        st.plotly_chart(fig4, use_container_width=True)

    with col5:
        st.subheader("Top Warehouses by Expense")
        loc_sum = (
            filtered_df.groupby("Locations")["Total Expenses"]
            .sum()
            .reset_index()
            .sort_values("Total Expenses", ascending=False)
            .head(7)
        )
        fig5 = px.bar(
            loc_sum,
            x="Total Expenses",
            y="Locations",
            orientation="h",
            color="Total Expenses",
            color_continuous_scale="Oranges",
        )
        st.plotly_chart(fig5, use_container_width=True)

    # Data Table View
    with st.expander("📄 View Filtered Raw Data"):
        st.dataframe(filtered_df, use_container_width=True)
