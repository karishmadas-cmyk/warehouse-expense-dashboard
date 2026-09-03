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
    # Load main expenses dataset
    df_exp = pd.read_excel("Monthly warehouse expenses.xlsx", sheet_name=0, header=1)
    df_exp["Month_Dt"] = pd.to_datetime(df_exp["Month"])
    df_exp["Month_Str"] = df_exp["Month_Dt"].dt.strftime("%B")
    df_exp["Year"] = df_exp["Month_Dt"].dt.year

    # Standardize column names if space columns were added to main sheet
    col_mapping = {
        "Total Space (Sq. Ft.)": "Total_Space",
        "Total Space": "Total_Space",
        "TOTAL SPACE": "Total_Space",
        "Additional Space (Sq. Ft.)": "Additional_Space",
        "Additional Space": "Additional_Space",
        "Occupied Space (Sq. Ft.)": "Occupied_Space",
    }
    df_exp.rename(columns=col_mapping, inplace=True)

    # Load Capacity/Master Sheet if available
    xls = pd.ExcelFile("Monthly warehouse expenses.xlsx")
    capacity_sheet_name = None
    for name in ["Warehouse_Master", "Warehouse_Capacity", "Capacity", "Master"]:
        if name in xls.sheet_names:
            capacity_sheet_name = name
            break

    if capacity_sheet_name:
        df_cap = pd.read_excel("Monthly warehouse expenses.xlsx", sheet_name=capacity_sheet_name)
        df_cap.rename(columns=col_mapping, inplace=True)
        if "Month" in df_cap.columns:
            df_cap["Month_Dt"] = pd.to_datetime(df_cap["Month"])
            df_cap["Month_Str"] = df_cap["Month_Dt"].dt.strftime("%B")
            df_cap["Year"] = df_cap["Month_Dt"].dt.year
    else:
        df_cap = pd.DataFrame()

    return df_exp, df_cap


df, df_cap = load_data()

# ------------------ APP HEADER ------------------
st.title("Warehouse Operational Expense & Space Dashboard FY 2026-27")
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
    "Select Zone", options=df["Zone"].unique()
)

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

# Dynamic Filtering Logic
filtered_df = df.copy()
filtered_cap = df_cap.copy() if not df_cap.empty else pd.DataFrame()

if selected_year:
    filtered_df = filtered_df[filtered_df["Year"].isin(selected_year)]
    if not filtered_cap.empty and "Year" in filtered_cap.columns:
        filtered_cap = filtered_cap[filtered_cap["Year"].isin(selected_year)]

if selected_month:
    filtered_df = filtered_df[filtered_df["Month_Str"].isin(selected_month)]
    if not filtered_cap.empty and "Month_Str" in filtered_cap.columns:
        filtered_cap = filtered_cap[filtered_cap["Month_Str"].isin(selected_month)]

if selected_zone:
    filtered_df = filtered_df[filtered_df["Zone"].isin(selected_zone)]
    if not filtered_cap.empty and "Zone" in filtered_cap.columns:
        filtered_cap = filtered_cap[filtered_cap["Zone"].isin(selected_zone)]

if selected_cust:
    filtered_df = filtered_df[filtered_df["Customer"].isin(selected_cust)]

if selected_loc:
    filtered_df = filtered_df[filtered_df["Locations"].isin(selected_loc)]
    if not filtered_cap.empty and "Locations" in filtered_cap.columns:
        filtered_cap = filtered_cap[filtered_cap["Locations"].isin(selected_loc)]


# ------------------ CALCULATE SPACE METRICS ------------------
# Deduplicate locations to prevent double counting across customer rows
if not filtered_cap.empty and "Total_Space" in filtered_cap.columns:
    total_space_sqft = filtered_cap["Total_Space"].sum()
elif "Total_Space" in filtered_df.columns:
    # Deduplicate by Location and Month to get correct space
    unique_spaces = filtered_df.drop_duplicates(subset=["Locations", "Month_Str"])
    total_space_sqft = unique_spaces["Total_Space"].sum()
else:
    total_space_sqft = 0

if "Occupied_Space" in filtered_df.columns:
    occupied_space_sqft = filtered_df["Occupied_Space"].sum()
elif "Total_Space" in filtered_df.columns:
    # If occupied isn't separated, calculate based on customer space allocations
    occupied_space_sqft = filtered_df.groupby("Locations")["Total_Space"].sum().sum()
else:
    occupied_space_sqft = 0

vacant_space_sqft = max(0, total_space_sqft - occupied_space_sqft)
occupancy_pct = (occupied_space_sqft / total_space_sqft * 100) if total_space_sqft > 0 else 0


# ------------------ TOP KPI METRIC CARDS ------------------
total_exp = filtered_df["Total Expenses"].sum() if not filtered_df.empty else 0

if selected_month:
    target_budget = sum(MONTHLY_BUDGETS.get(m, 0) for m in selected_month)
else:
    active_months = filtered_df["Month_Str"].unique() if not filtered_df.empty else MONTHLY_BUDGETS.keys()
    target_budget = sum(MONTHLY_BUDGETS.get(m, 0) for m in active_months)

expense_diff = total_exp - target_budget

if expense_diff > 0:
    delta_text = f"▲ {format_inr(abs(expense_diff))} Above Budget"
    delta_color_style = "#d9383a"
else:
    delta_text = f"▼ {format_inr(abs(expense_diff))} Below Budget"
    delta_color_style = "#28a745"

# Row 1 KPIs (Expenses & Counts)
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
    st.metric("Total Warehouses", filtered_df["Locations"].nunique() if not filtered_df.empty else 0)

with col_kpi3:
    st.metric("Total Customers", filtered_df["Customer"].nunique() if not filtered_df.empty else 0)

st.markdown("<br>", unsafe_allow_html=True)

# Row 2 KPIs (Space Analytics)
col_sp1, col_sp2, col_sp3 = st.columns(3)

with col_sp1:
    st.metric("📦 Total Space", format_sqft(total_space_sqft))

with col_sp2:
    st.metric("🟢 Occupied Space", format_sqft(occupied_space_sqft), delta=f"{occupancy_pct:.1f}% Occupied")

with col_sp3:
    st.metric("🔴 Vacant Space", format_sqft(vacant_space_sqft), delta=f"{100-occupancy_pct:.1f}% Vacant", delta_color="inverse")

st.markdown("---")

if filtered_df.empty:
    st.warning("⚠️ No data available for the selected combination of filters.")
else:
    # ------------------ SPACE CAPACITY TREND & BREAKDOWN ------------------
    if total_space_sqft > 0:
        st.subheader("📐 Warehouse Space Capacity & Occupancy Analysis")
        col_sp_chart1, col_sp_chart2 = st.columns([1.2, 1])

        with col_sp_chart1:
            # Space Trend Monthwise
            if not filtered_cap.empty and "Total_Space" in filtered_cap.columns:
                m_space = filtered_cap.groupby(["Month_Dt", "Month_Str"])["Total_Space"].sum().reset_index()
            else:
                m_space = filtered_df.drop_duplicates(subset=["Locations", "Month_Str"]).groupby(["Month_Dt", "Month_Str"])["Total_Space"].sum().reset_index()

            m_occ = filtered_df.groupby(["Month_Dt", "Month_Str"])["Occupied_Space"].sum().reset_index() if "Occupied_Space" in filtered_df.columns else m_space.copy()
            
            m_space_merged = pd.merge(m_space, m_occ, on=["Month_Dt", "Month_Str"], how="left").fillna(0)
            m_space_merged.sort_values("Month_Dt", inplace=True)
            m_space_merged["Vacant_Space"] = m_space_merged["Total_Space"] - m_space_merged.get("Occupied_Space", 0)

            fig_space = go.Figure()
            fig_space.add_trace(go.Bar(x=m_space_merged["Month_Str"], y=m_space_merged["Total_Space"], name="Total Space", marker_color="#0078D4"))
            fig_space.add_trace(go.Bar(x=m_space_merged["Month_Str"], y=m_space_merged.get("Occupied_Space", 0), name="Occupied Space", marker_color="#28a745"))

            fig_space.update_layout(
                barmode="group",
                height=350,
                title="Monthwise Total vs. Occupied Space (Sq. Ft.)",
                margin=dict(l=20, r=20, t=40, b=20),
            )
            st.plotly_chart(fig_space, use_container_width=True)

        with col_sp_chart2:
            # Top Locations with Most Vacant Space
            if "Occupied_Space" in filtered_df.columns:
                loc_tot = filtered_df.drop_duplicates(subset=["Locations", "Month_Str"]).groupby("Locations")["Total_Space"].mean()
                loc_occ = filtered_df.groupby("Locations")["Occupied_Space"].mean()
                loc_vac = (loc_tot - loc_occ).reset_index(name="Vacant_Space").sort_values("Vacant_Space", ascending=True).tail(10)
            else:
                loc_vac = pd.DataFrame(columns=["Locations", "Vacant_Space"])

            if not loc_vac.empty:
                fig_vac = px.bar(
                    loc_vac,
                    x="Vacant_Space",
                    y="Locations",
                    orientation="h",
                    title="Top Warehouses by Vacant Space (Sq. Ft.)",
                    color_discrete_sequence=["#d9383a"],
                    text=loc_vac["Vacant_Space"].apply(lambda x: f"{x:,.0f}"),
                )
                fig_vac.update_traces(textposition="outside")
                fig_vac.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20), yaxis_title="")
                st.plotly_chart(fig_vac, use_container_width=True)

        st.markdown("---")

    # ------------------ ROW 1: Expense Trend & Zone ------------------
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
        fig1.update_traces(textposition="top center", line=dict(width=3, color="#0078D4"))
        fig1.update_layout(height=350, margin=dict(l=20, r=20, t=30, b=20))

        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("🌍 Expense Distribution by Zone")

        z_sum = filtered_df.groupby("Zone")["Total Expenses"].sum().reset_index()

        fig2 = px.pie(
            z_sum,
            values="Total Expenses",
            names="Zone",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Set2,
        )

        fig2.update_traces(textinfo="percent+label")
        fig2.update_layout(height=350, showlegend=False, margin=dict(l=20, r=20, t=30, b=20))

        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # ------------------ ROW 2: Categories & Customers ------------------
    col3, col4 = st.columns([1, 1])

    with col3:
        st.subheader("📊 Top 10 Expense Categories")

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

        existing_cat_cols = [c for c in cat_cols if c in filtered_df.columns]
        cat_sum = filtered_df[existing_cat_cols].sum().reset_index()
        cat_sum.columns = ["Category", "Expense"]

        cat_sum = cat_sum[cat_sum["Expense"] > 0]
        cat_sum = cat_sum.nlargest(10, "Expense").sort_values("Expense", ascending=True)
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
        fig3.update_layout(height=380, yaxis_title="", margin=dict(l=20, r=20, t=30, b=20))

        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("👥 Top 10 Customers")

        cust_sum = filtered_df.groupby("Customer")["Total Expenses"].sum().reset_index()
        cust_sum = cust_sum.nlargest(10, "Total Expenses").sort_values("Total Expenses", ascending=True)
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
        fig4.update_layout(height=380, yaxis_title="", margin=dict(l=20, r=20, t=30, b=20))

        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")

    # ------------------ ROW 3: Warehouses & Detail Table ------------------
    col5, col6 = st.columns([1, 1])

    with col5:
        st.subheader("🏬 Top 10 Warehouses")

        loc_sum = (
            filtered_df.groupby("Locations")["Total Expenses"]
            .sum()
            .reset_index()
            .sort_values("Total Expenses", ascending=True)
            .tail(10)
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
        fig5.update_layout(height=380, yaxis_title="", margin=dict(l=20, r=20, t=30, b=20))

        st.plotly_chart(fig5, use_container_width=True)

    with col6:
        st.subheader("📋 EXPENSE DETAIL SUMMARY")

        detail_df = (
            filtered_df.groupby(["Customer", "Locations", "Year", "Month_Str"])["Total Expenses"]
            .sum()
            .reset_index()
            .sort_values(by="Total Expenses", ascending=False)
        )

        detail_df.columns = ["Customer", "Locations", "Year", "Month", "Total Expense"]
        formatted_detail_df = detail_df.copy()
        formatted_detail_df["Total Expense"] = formatted_detail_df["Total Expense"].apply(lambda x: f"₹ {x:,.0f}")

        st.dataframe(formatted_detail_df, use_container_width=True, height=310)

    # Detailed Full Dataset View
    with st.expander("📄 View Full Line-Item Data Table"):
        st.dataframe(filtered_df, use_container_width=True)
