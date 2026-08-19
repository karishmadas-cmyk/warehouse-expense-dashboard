import pandas as pd
import plotly.express as px
import streamlit as st

# Set Page Title & Layout
st.set_page_config(
    page_title="Warehouse Operational Expense Dashboard FY 2026-27",
    layout="wide",
)

# -----------------------------------------------------------------------------
# MONTHLY BUDGET CONFIGURATION (In INR)
# Adjust these values to match your target budget per month
# -----------------------------------------------------------------------------
MONTHLY_BUDGETS = {
    "April": 1.5e7,      # ₹7.14 Cr
    "May": 1.4e7,        # ₹6.84 Cr
    "June": 1.6e7,       # ₹7.13 Cr
    "July": 1.5e7,       # ₹7.48 Cr
    "August": 1.5e7,     # ₹7.45 Cr
    "September": 1.7e7,  # ₹7.48 Cr
    "October": 1.8e7,    # ₹7.98 Cr
    "November": 1.5e7,   # ₹7.89 Cr
    "December": 1.6e7,   # ₹8.48 Cr
    "January": 1.5e7,    # ₹8.73 Cr
    "February": 1.4e7,   # ₹8.82 Cr
    "March": 1.5e7       # ₹9.68 Cr
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

# ------------------ TOP KPI METRIC CARDS ------------------
total_exp = filtered_df["Total Expenses"].sum() if not filtered_df.empty else 0

# Dynamic Budget Calculation based on Selected Month Filter
if selected_month:
    target_budget = sum(MONTHLY_BUDGETS.get(m, 0) for m in selected_month)
else:
    # If no month is selected, compute target budget based on visible/filtered data months
    active_months = filtered_df["Month_Str"].unique() if not filtered_df.empty else MONTHLY_BUDGETS.keys()
    target_budget = sum(MONTHLY_BUDGETS.get(m, 0) for m in active_months)

# Budget Variance & Color Logic
expense_diff = total_exp - target_budget

if expense_diff > 0:
    delta_text = f"▲ {format_inr(abs(expense_diff))} Above Budget"
    delta_color_style = "#d9383a"  # Red for Above Budget
else:
    delta_text = f"▼ {format_inr(abs(expense_diff))} Below Budget"
    delta_color_style = "#28a745"  # Green for Below Budget

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

with col_kpi1:
    st.markdown(f"""
        <div style="background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 10px 15px;">
            <span style="font-size: 14px; color: #555555;">Total Expense</span>
            <div style="font-size: 28px; font-weight: bold; color: #1f1f1f; margin-top: 2px;">{format_inr(total_exp)}</div>
            <div style="font-size: 13px; font-weight: 600; color: {delta_color_style}; margin-top: 4px;">
                {delta_text}
            </div>
        </div>
    """, unsafe_allow_html=True)

with col_kpi2:
    st.metric("Total Warehouses", filtered_df["Locations"].nunique() if not filtered_df.empty else 0)

with col_kpi3:
    st.metric("Total Customers", filtered_df["Customer"].nunique() if not filtered_df.empty else 0)

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
