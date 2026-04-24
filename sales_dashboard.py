import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from gspread_dataframe import get_as_dataframe

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dunkin' Multi-Store Sales 2021–2024",
    page_icon="🍩",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #1a1a2e !important;
    }
    .stApp { background: #f5f6fa; }

    section[data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 2px solid #f0f0f5;
        box-shadow: 2px 0 12px rgba(0,0,0,0.04);
    }

    /* KPI cards */
    div[data-testid="metric-container"] {
        background: #ffffff;
        border: none;
        border-radius: 20px;
        padding: 1.4rem 1.6rem;
        position: relative;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        transition: transform 0.2s;
    }
    div[data-testid="metric-container"]::after {
        content: '';
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 4px;
        background: linear-gradient(90deg, #ff6b00, #ff9500);
        border-radius: 0 0 20px 20px;
    }
    div[data-testid="metric-container"] label {
        color: #888899 !important;
        font-size: 0.68rem !important;
        letter-spacing: 0.14em !important;
        text-transform: uppercase !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-weight: 600 !important;
    }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #1a1a2e !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
    }

    h1 {
        color: #1a1a2e !important;
        font-weight: 800 !important;
        letter-spacing: -0.04em !important;
        font-size: 2.2rem !important;
        line-height: 1.1 !important;
    }
    h2, h3 {
        color: #1a1a2e !important;
        font-weight: 700 !important;
    }
    h4 { color: #444466 !important; font-weight: 600 !important; }
    p, span, li { color: #333355 !important; }
    hr { border-color: #ebebf5 !important; margin: 1.5rem 0 !important; }

    /* Tabs */
    button[data-baseweb="tab"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        color: #666688 !important;
        letter-spacing: 0.02em !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #ff6b00 !important;
    }
    div[data-baseweb="tab-highlight"] {
        background-color: #ff6b00 !important;
    }

    /* Selectbox / inputs */
    div[data-baseweb="select"] > div {
        background: #f8f8fc !important;
        border-color: #e0e0ee !important;
        border-radius: 12px !important;
        color: #1a1a2e !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    /* Slider */
    div[data-testid="stSlider"] label { color: #444466 !important; }

    /* Expander */
    details {
        background: #ffffff !important;
        border: 1px solid #ebebf5 !important;
        border-radius: 16px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    }

    /* Chart containers */
    .chart-card {
        background: #ffffff;
        border-radius: 20px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        margin-bottom: 1rem;
    }

    .section-tag {
        display: inline-block;
        background: #fff3e8;
        color: #ff6b00;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.62rem;
        font-weight: 600;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        padding: 3px 10px;
        border-radius: 99px;
        margin-bottom: 6px;
    }

    .kpi-group-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.6rem;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: #aaaacc;
        margin-bottom: 4px;
        margin-top: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ── Chart theme ───────────────────────────────────────────────────────────────
PALETTE = ["#ff6b00","#ff9500","#ffb700","#00b4d8","#0077b6",
           "#06d6a0","#ef233c","#8338ec","#3a86ff","#fb5607"]

ORANGE_SEQ = ["#fff3e8","#ffd4a3","#ffab4f","#ff8500","#ff6b00","#cc4400"]
BLUE_SEQ   = ["#e8f4ff","#a3d4ff","#4fabff","#0077b6","#005580"]

def T(fig, height=400, margin=None, bgcolor="#ffffff", **kwargs):
    if margin is None:
        margin = dict(l=10, r=20, t=40, b=20)
    fig.update_layout(
        paper_bgcolor=bgcolor,
        plot_bgcolor="#f8f8fc",
        font=dict(color="#333355", family="Plus Jakarta Sans", size=12),
        height=height,
        margin=margin,
        **kwargs,
    )
    fig.update_xaxes(gridcolor="#ebebf5", linecolor="#e0e0ee",
                     zerolinecolor="#e0e0ee", tickfont=dict(color="#555577", size=11))
    fig.update_yaxes(gridcolor="#ebebf5", linecolor="#e0e0ee",
                     zerolinecolor="#e0e0ee", tickfont=dict(color="#555577", size=11))
    return fig

def fmt(v):
    if v >= 1_000_000: return f"${v/1_000_000:.2f}M"
    if v >= 1_000:     return f"${v/1_000:.1f}K"
    return f"${v:.2f}"

# ── File path ─────────────────────────────────────────────────────────────────
import gspread
from gspread_dataframe import get_as_dataframe

SHEET_URL = "YOUR_GOOGLE_SHEET_URL_HERE"

@st.cache_data(ttl=60)
def load_data():
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    sheet = gc.open_by_url(SHEET_URL)
    worksheet = sheet.get_worksheet(0)
    df = get_as_dataframe(worksheet, evaluate_formulas=True).dropna(how="all")
    df.columns = df.columns.str.strip()

    for col in ["TrDate","TrWeekEndDate"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    num_cols = ["GrossSales","DiscountRefund","NetSalesPlusTax","NewsPaperSales",
                "WholeSalesSale","NetSaleMinusPaper","SalesTax","NetSalesMinusTax",
                "CustomerCount","DunkinSales","BaskinSales"]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "TrDate" in df.columns:
        df["Year"]      = df["TrDate"].dt.year
        df["Month"]     = df["TrDate"].dt.month
        df["MonthName"] = df["TrDate"].dt.strftime("%b")
        df["YearMonth"] = df["TrDate"].dt.to_period("M").astype(str)
        df["Quarter"]   = df["TrDate"].dt.quarter.apply(lambda x: f"Q{x}")
        df["WeekDay"]   = df["TrDate"].dt.day_name()
        df["YearQ"]     = df["TrDate"].dt.to_period("Q").astype(str)

    if "PCNumber" in df.columns:
        df["PCNumber"] = df["PCNumber"].astype(str)

    if "GrossSales" in df.columns and "DiscountRefund" in df.columns:
        df["DiscountPct"] = (df["DiscountRefund"].abs() / df["GrossSales"].replace(0, float("nan")) * 100).fillna(0).round(2)

    if "DunkinSales" in df.columns and "BaskinSales" in df.columns:
        df["TotalBrandSales"] = df["DunkinSales"].fillna(0) + df["BaskinSales"].fillna(0)

    return df

df_raw = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🍩 Sales Analytics")
    st.markdown("**Multi-Store · 2021–2024**")
    st.markdown("---")
    st.markdown("### 🔍 Filters")

    # Year
    years = ["All"] + sorted(df_raw["Year"].dropna().unique().astype(int).tolist(), reverse=True) if "Year" in df_raw.columns else ["All"]
    sel_year = st.selectbox("📅 Year", years)

    # Quarter
    quarters = ["All","Q1","Q2","Q3","Q4"]
    sel_q = st.selectbox("📆 Quarter", quarters)

    # PC Number (Store)
    if "PCNumber" in df_raw.columns:
        pcs = ["All"] + sorted(df_raw["PCNumber"].dropna().unique().tolist())
        sel_pc = st.selectbox("🏪 Store (PC Number)", pcs)
    else:
        sel_pc = "All"

    # Date range
    if "TrDate" in df_raw.columns:
        min_d = df_raw["TrDate"].min().date()
        max_d = df_raw["TrDate"].max().date()
        date_range = st.date_input("📅 Custom Date Range", value=(min_d, max_d),
                                   min_value=min_d, max_value=max_d)
    else:
        date_range = None

    st.markdown("---")
    st.caption("File loaded ✅")

# ── Apply filters ─────────────────────────────────────────────────────────────
df = df_raw.copy()
if sel_year != "All" and "Year" in df.columns:
    df = df[df["Year"] == int(sel_year)]
if sel_q != "All" and "Quarter" in df.columns:
    df = df[df["Quarter"] == sel_q]
if sel_pc != "All" and "PCNumber" in df.columns:
    df = df[df["PCNumber"] == sel_pc]
if date_range and len(date_range) == 2 and "TrDate" in df.columns:
    df = df[(df["TrDate"].dt.date >= date_range[0]) & (df["TrDate"].dt.date <= date_range[1])]

st.sidebar.markdown(f"**{len(df):,}** of **{len(df_raw):,}** rows")


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<span class="section-tag">Multi-Store · PC 301798 · 343672 · 332860</span>', unsafe_allow_html=True)
st.markdown("# 🍩 Dunkin' Sales Intelligence 2021–2024")
st.markdown("---")

# ── KPI Row 1 — Revenue ───────────────────────────────────────────────────────
st.markdown('<p class="kpi-group-label">💰 Revenue Metrics</p>', unsafe_allow_html=True)
k1,k2,k3,k4,k5 = st.columns(5)

gross      = df["GrossSales"].sum()        if "GrossSales"      in df.columns else 0
net_tax    = df["NetSalesMinusTax"].sum()  if "NetSalesMinusTax" in df.columns else 0
discount   = df["DiscountRefund"].sum()    if "DiscountRefund"   in df.columns else 0
tax        = df["SalesTax"].sum()          if "SalesTax"         in df.columns else 0
dunkin_s   = df["DunkinSales"].sum()       if "DunkinSales"      in df.columns else 0

k1.metric("Gross Sales",        fmt(gross))
k2.metric("Net Sales (ex-Tax)", fmt(net_tax))
k3.metric("Discounts / Refunds",fmt(abs(discount)))
k4.metric("Sales Tax",          fmt(tax))
k5.metric("Dunkin' Sales",      fmt(dunkin_s))

st.markdown('<p class="kpi-group-label">📊 Volume & Operations</p>', unsafe_allow_html=True)
k6,k7,k8,k9,k10 = st.columns(5)

customers  = df["CustomerCount"].sum()     if "CustomerCount"    in df.columns else 0
baskin_s   = df["BaskinSales"].sum()       if "BaskinSales"      in df.columns else 0
newspaper  = df["NewsPaperSales"].sum()    if "NewsPaperSales"   in df.columns else 0
wholesale  = df["WholeSalesSale"].sum()    if "WholeSalesSale"   in df.columns else 0
avg_check  = (gross / customers)           if customers > 0 else 0

k6.metric("Total Customers",    f"{customers:,.0f}")
k7.metric("Avg Check Value",    f"${avg_check:.2f}")
k8.metric("Baskin Sales",       fmt(baskin_s))
k9.metric("Newspaper Sales",    fmt(newspaper))
k10.metric("Wholesale Sales",   fmt(wholesale))

st.markdown("---")

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Revenue Trends",
    "🏪 Store Comparison",
    "🍩 Dunkin vs Baskin",
    "📉 Discounts & Tax",
    "📅 Time Patterns",
    "📋 Data Explorer",
])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — REVENUE TRENDS
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### Revenue Over Time")

    # Monthly gross sales trend
    if "YearMonth" in df.columns and "GrossSales" in df.columns:
        monthly = df.groupby("YearMonth").agg(
            GrossSales=("GrossSales","sum"),
            NetSales=("NetSalesMinusTax","sum"),
            Customers=("CustomerCount","sum"),
        ).reset_index().sort_values("YearMonth")

        fig_m = go.Figure()
        fig_m.add_trace(go.Scatter(
            x=monthly["YearMonth"], y=monthly["GrossSales"],
            name="Gross Sales", fill="tozeroy",
            fillcolor="rgba(255,107,0,0.1)",
            line=dict(color="#ff6b00", width=2.5),
            mode="lines",
        ))
        fig_m.add_trace(go.Scatter(
            x=monthly["YearMonth"], y=monthly["NetSales"],
            name="Net Sales", fill="tozeroy",
            fillcolor="rgba(0,119,182,0.08)",
            line=dict(color="#0077b6", width=2, dash="dot"),
            mode="lines",
        ))
        fig_m.update_layout(legend=dict(orientation="h", y=1.05))
        T(fig_m, height=380, title="Monthly Gross vs Net Sales",
          title_font=dict(size=15, color="#1a1a2e"))
        st.plotly_chart(fig_m, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        # Yearly bar
        if "Year" in df.columns and "GrossSales" in df.columns:
            yr = df.groupby("Year")["GrossSales"].sum().reset_index()
            yr.columns = ["Year","GrossSales"]
            yr["Label"] = yr["GrossSales"].apply(fmt)
            fig_yr = px.bar(yr, x="Year", y="GrossSales",
                            color="GrossSales", color_continuous_scale=ORANGE_SEQ,
                            text="Label", title="Annual Gross Sales")
            fig_yr.update_traces(textposition="outside")
            T(fig_yr, height=360, coloraxis_showscale=False,
              title_font=dict(size=14, color="#1a1a2e"),
              margin=dict(l=10,r=10,t=50,b=40))
            st.plotly_chart(fig_yr, use_container_width=True)

    with col2:
        # Quarterly
        if "YearQ" in df.columns and "GrossSales" in df.columns:
            qdf = df.groupby("YearQ")["GrossSales"].sum().reset_index().sort_values("YearQ")
            fig_q = px.bar(qdf, x="YearQ", y="GrossSales",
                           color="GrossSales", color_continuous_scale=ORANGE_SEQ,
                           text=qdf["GrossSales"].apply(fmt),
                           title="Quarterly Gross Sales")
            fig_q.update_traces(textposition="outside")
            fig_q.update_xaxes(tickangle=-45)
            T(fig_q, height=360, coloraxis_showscale=False,
              title_font=dict(size=14, color="#1a1a2e"),
              margin=dict(l=10,r=10,t=50,b=80))
            st.plotly_chart(fig_q, use_container_width=True)

    # Customer count over time
    if "YearMonth" in df.columns and "CustomerCount" in df.columns:
        st.markdown("### Customer Count Trend")
        cust = df.groupby("YearMonth")["CustomerCount"].sum().reset_index().sort_values("YearMonth")
        fig_cust = px.area(cust, x="YearMonth", y="CustomerCount",
                           color_discrete_sequence=["#0077b6"],
                           title="Monthly Customer Count")
        fig_cust.update_traces(fill="tozeroy", fillcolor="rgba(0,119,182,0.1)",
                                line=dict(width=2))
        T(fig_cust, height=320, title_font=dict(size=14, color="#1a1a2e"))
        st.plotly_chart(fig_cust, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — STORE COMPARISON
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Store Performance Comparison")

    if "PCNumber" in df.columns:
        store_agg = df.groupby("PCNumber").agg(
            GrossSales=("GrossSales","sum"),
            NetSales=("NetSalesMinusTax","sum"),
            Customers=("CustomerCount","sum"),
            DunkinSales=("DunkinSales","sum"),
            BaskinSales=("BaskinSales","sum"),
            Discount=("DiscountRefund","sum"),
        ).reset_index()
        store_agg["AvgCheck"] = (store_agg["GrossSales"] / store_agg["Customers"].replace(0,pd.NA)).round(2)
        store_agg["DiscountPct"] = (store_agg["Discount"].abs() / store_agg["GrossSales"].replace(0, float("nan")) * 100).fillna(0).round(1)

        col1, col2 = st.columns(2)

        with col1:
            fig_s1 = px.bar(store_agg, x="PCNumber", y="GrossSales",
                            color="PCNumber", color_discrete_sequence=PALETTE,
                            text=store_agg["GrossSales"].apply(fmt),
                            title="Gross Sales by Store")
            fig_s1.update_traces(textposition="outside")
            T(fig_s1, height=360, showlegend=False,
              title_font=dict(size=14, color="#1a1a2e"),
              margin=dict(l=10,r=10,t=50,b=40))
            st.plotly_chart(fig_s1, use_container_width=True)

        with col2:
            fig_s2 = px.bar(store_agg, x="PCNumber", y="Customers",
                            color="PCNumber", color_discrete_sequence=PALETTE,
                            text=store_agg["Customers"].apply(lambda x: f"{x:,.0f}"),
                            title="Total Customers by Store")
            fig_s2.update_traces(textposition="outside")
            T(fig_s2, height=360, showlegend=False,
              title_font=dict(size=14, color="#1a1a2e"),
              margin=dict(l=10,r=10,t=50,b=40))
            st.plotly_chart(fig_s2, use_container_width=True)

        # Avg check and discount side by side
        col3, col4 = st.columns(2)
        with col3:
            fig_s3 = px.bar(store_agg, x="PCNumber", y="AvgCheck",
                            color="PCNumber", color_discrete_sequence=PALETTE,
                            text=store_agg["AvgCheck"].apply(lambda x: f"${x:.2f}"),
                            title="Average Check Value by Store")
            fig_s3.update_traces(textposition="outside")
            T(fig_s3, height=340, showlegend=False,
              title_font=dict(size=14, color="#1a1a2e"),
              margin=dict(l=10,r=10,t=50,b=40))
            st.plotly_chart(fig_s3, use_container_width=True)

        with col4:
            fig_s4 = px.bar(store_agg, x="PCNumber", y="DiscountPct",
                            color="PCNumber", color_discrete_sequence=PALETTE,
                            text=store_agg["DiscountPct"].apply(lambda x: f"{x:.1f}%"),
                            title="Discount % by Store")
            fig_s4.update_traces(textposition="outside")
            T(fig_s4, height=340, showlegend=False,
              title_font=dict(size=14, color="#1a1a2e"),
              margin=dict(l=10,r=10,t=50,b=40))
            st.plotly_chart(fig_s4, use_container_width=True)

        # Store trend over time
        st.markdown("### Store Revenue Trend Over Time")
        if "YearMonth" in df.columns:
            store_time = df.groupby(["YearMonth","PCNumber"])["GrossSales"].sum().reset_index().sort_values("YearMonth")
            fig_st = px.line(store_time, x="YearMonth", y="GrossSales",
                             color="PCNumber", color_discrete_sequence=PALETTE,
                             markers=True, title="Monthly Sales per Store",
                             line_shape="spline")
            fig_st.update_traces(line=dict(width=2.5), marker=dict(size=5))
            T(fig_st, height=400, title_font=dict(size=14, color="#1a1a2e"),
              legend=dict(orientation="h", y=1.08))
            st.plotly_chart(fig_st, use_container_width=True)

        # Radar chart — store metrics
        st.markdown("### Store Metrics Radar")
        metrics = ["GrossSales","NetSales","Customers","DunkinSales","BaskinSales"]
        metrics = [m for m in metrics if m in store_agg.columns]
        if len(metrics) >= 3:
            norm = store_agg.copy()
            for m in metrics:
                max_v = norm[m].max()
                norm[m] = (norm[m] / max_v * 100) if max_v > 0 else 0
            fig_radar = go.Figure()
            for i, row in norm.iterrows():
                fig_radar.add_trace(go.Scatterpolar(
                    r=[row[m] for m in metrics] + [row[metrics[0]]],
                    theta=metrics + [metrics[0]],
                    fill="toself",
                    name=f"PC {row['PCNumber']}",
                    line_color=PALETTE[i % len(PALETTE)],
                    fillcolor="rgba(255,107,0,0.15)" if i == 0 else ("rgba(255,149,0,0.15)" if i == 1 else "rgba(0,119,182,0.15)"),
                ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0,100],
                                           gridcolor="#ebebf5", linecolor="#e0e0ee"),
                           angularaxis=dict(gridcolor="#ebebf5", linecolor="#e0e0ee")),
                paper_bgcolor="#ffffff",
                font=dict(color="#333355", family="Plus Jakarta Sans"),
                height=420,
                legend=dict(orientation="h", y=-0.15),
                title="Store Performance Radar (normalised to 100)",
                title_font=dict(size=14, color="#1a1a2e"),
            )
            st.plotly_chart(fig_radar, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — DUNKIN vs BASKIN
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### Dunkin' vs Baskin-Robbins Brand Analysis")

    if "DunkinSales" in df.columns and "BaskinSales" in df.columns:

        col1, col2 = st.columns(2)

        with col1:
            total_d = df["DunkinSales"].sum()
            total_b = df["BaskinSales"].sum()
            fig_pie = px.pie(
                names=["Dunkin'","Baskin-Robbins"],
                values=[total_d, total_b],
                color_discrete_sequence=["#ff6b00","#e63946"],
                hole=0.55,
                title="Brand Sales Split (Total)",
            )
            fig_pie.update_traces(textinfo="percent+label", textposition="outside")
            T(fig_pie, height=360, title_font=dict(size=14, color="#1a1a2e"),
              showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            if "YearMonth" in df.columns:
                brand_m = df.groupby("YearMonth").agg(
                    Dunkin=("DunkinSales","sum"),
                    Baskin=("BaskinSales","sum"),
                ).reset_index().sort_values("YearMonth")
                fig_brand = go.Figure()
                fig_brand.add_trace(go.Bar(x=brand_m["YearMonth"], y=brand_m["Dunkin"],
                                           name="Dunkin'", marker_color="#ff6b00"))
                fig_brand.add_trace(go.Bar(x=brand_m["YearMonth"], y=brand_m["Baskin"],
                                           name="Baskin-Robbins", marker_color="#e63946"))
                fig_brand.update_layout(barmode="stack",
                                        legend=dict(orientation="h", y=1.08))
                T(fig_brand, height=360, title="Monthly Dunkin' vs Baskin Sales",
                  title_font=dict(size=14, color="#1a1a2e"))
                st.plotly_chart(fig_brand, use_container_width=True)

        # Year over year brand split
        if "Year" in df.columns:
            brand_yr = df.groupby("Year").agg(
                Dunkin=("DunkinSales","sum"),
                Baskin=("BaskinSales","sum"),
            ).reset_index()
            brand_yr["DunkinPct"] = (brand_yr["Dunkin"] / (brand_yr["Dunkin"]+brand_yr["Baskin"]) * 100).round(1)
            brand_yr["BaskinPct"] = (100 - brand_yr["DunkinPct"]).round(1)

            col3, col4 = st.columns(2)
            with col3:
                fig_by = px.bar(brand_yr, x="Year",
                                y=["Dunkin","Baskin"],
                                color_discrete_sequence=["#ff6b00","#e63946"],
                                barmode="group", title="Annual Brand Sales",
                                text_auto=False)
                T(fig_by, height=350, title_font=dict(size=14, color="#1a1a2e"),
                  legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig_by, use_container_width=True)

            with col4:
                fig_pct = px.bar(brand_yr, x="Year",
                                 y=["DunkinPct","BaskinPct"],
                                 color_discrete_sequence=["#ff6b00","#e63946"],
                                 barmode="stack", title="Brand Share % by Year")
                fig_pct.update_layout(yaxis_title="Share %")
                T(fig_pct, height=350, title_font=dict(size=14, color="#1a1a2e"),
                  legend=dict(orientation="h", y=1.1))
                st.plotly_chart(fig_pct, use_container_width=True)

        # Brand by store
        if "PCNumber" in df.columns:
            st.markdown("### Brand Sales by Store")
            brand_store = df.groupby("PCNumber").agg(
                Dunkin=("DunkinSales","sum"),
                Baskin=("BaskinSales","sum"),
            ).reset_index()
            fig_bs = px.bar(brand_store, x="PCNumber",
                            y=["Dunkin","Baskin"],
                            color_discrete_sequence=["#ff6b00","#e63946"],
                            barmode="group", title="Dunkin' vs Baskin by Store",
                            text_auto=False)
            T(fig_bs, height=360, title_font=dict(size=14, color="#1a1a2e"),
              legend=dict(orientation="h", y=1.1),
              margin=dict(l=10,r=10,t=60,b=40))
            st.plotly_chart(fig_bs, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — DISCOUNTS & TAX
# ════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### Discounts, Refunds & Tax Analysis")

    col1, col2 = st.columns(2)

    with col1:
        if "YearMonth" in df.columns and "DiscountRefund" in df.columns:
            disc_m = df.groupby("YearMonth")["DiscountRefund"].sum().reset_index().sort_values("YearMonth")
            fig_disc = px.bar(disc_m, x="YearMonth", y="DiscountRefund",
                              color="DiscountRefund",
                              color_continuous_scale=["#ff6b00","#ffb700","#ebebf5"],
                              title="Monthly Discount / Refund")
            fig_disc.update_xaxes(tickangle=-45)
            T(fig_disc, height=360, coloraxis_showscale=False,
              title_font=dict(size=14, color="#1a1a2e"),
              margin=dict(l=10,r=10,t=50,b=80))
            st.plotly_chart(fig_disc, use_container_width=True)

    with col2:
        if "YearMonth" in df.columns and "SalesTax" in df.columns:
            tax_m = df.groupby("YearMonth")["SalesTax"].sum().reset_index().sort_values("YearMonth")
            fig_tax = px.area(tax_m, x="YearMonth", y="SalesTax",
                              color_discrete_sequence=["#0077b6"],
                              title="Monthly Sales Tax Collected")
            fig_tax.update_traces(fill="tozeroy", fillcolor="rgba(0,119,182,0.1)",
                                   line=dict(width=2))
            fig_tax.update_xaxes(tickangle=-45)
            T(fig_tax, height=360, title_font=dict(size=14, color="#1a1a2e"),
              margin=dict(l=10,r=10,t=50,b=80))
            st.plotly_chart(fig_tax, use_container_width=True)

    # Gross vs Net waterfall by year
    if "Year" in df.columns:
        st.markdown("### Gross → Net Sales Waterfall by Year")
        wf = df.groupby("Year").agg(
            Gross=("GrossSales","sum"),
            Discount=("DiscountRefund","sum"),
            Tax=("SalesTax","sum"),
            Net=("NetSalesMinusTax","sum"),
        ).reset_index()

        fig_wf = go.Figure()
        fig_wf.add_trace(go.Bar(x=wf["Year"].astype(str), y=wf["Gross"],
                                name="Gross Sales", marker_color="#ff6b00",
                                text=wf["Gross"].apply(fmt), textposition="outside"))
        fig_wf.add_trace(go.Bar(x=wf["Year"].astype(str), y=wf["Discount"],
                                name="Discount/Refund", marker_color="#ffb700",
                                text=wf["Discount"].apply(fmt), textposition="outside"))
        fig_wf.add_trace(go.Bar(x=wf["Year"].astype(str), y=wf["Net"],
                                name="Net Sales", marker_color="#0077b6",
                                text=wf["Net"].apply(fmt), textposition="outside"))
        fig_wf.update_layout(barmode="group",
                              legend=dict(orientation="h", y=1.08))
        T(fig_wf, height=400, title="Annual: Gross vs Discount vs Net Sales",
          title_font=dict(size=14, color="#1a1a2e"),
          margin=dict(l=10,r=10,t=60,b=40))
        st.plotly_chart(fig_wf, use_container_width=True)

    # Discount % heatmap by store × year
    if "PCNumber" in df.columns and "Year" in df.columns:
        st.markdown("### Discount Rate Heatmap (Store × Year)")
        disc_heat = df.groupby(["PCNumber","Year"]).agg(
            Gross=("GrossSales","sum"),
            Disc=("DiscountRefund","sum"),
        ).reset_index()
        disc_heat["DiscPct"] = (disc_heat["Disc"].abs() / disc_heat["Gross"].replace(0,pd.NA) * 100).round(1)
        pivot_disc = disc_heat.pivot_table(index="PCNumber", columns="Year", values="DiscPct", fill_value=0)
        fig_dh = px.imshow(pivot_disc.round(1),
                           color_continuous_scale=ORANGE_SEQ,
                           text_auto=True, aspect="auto",
                           title="Discount % by Store × Year")
        T(fig_dh, height=300, coloraxis_showscale=True,
          title_font=dict(size=14, color="#1a1a2e"),
          margin=dict(l=10,r=10,t=50,b=10))
        st.plotly_chart(fig_dh, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 5 — TIME PATTERNS
# ════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("### Sales Patterns by Time")

    col1, col2 = st.columns(2)

    with col1:
        if "WeekDay" in df.columns and "GrossSales" in df.columns:
            day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
            dow = df.groupby("WeekDay")["GrossSales"].sum().reindex(day_order).reset_index()
            dow.columns = ["Day","Sales"]
            fig_dow = px.bar(dow, x="Day", y="Sales",
                             color="Sales", color_continuous_scale=ORANGE_SEQ,
                             text=dow["Sales"].apply(fmt),
                             title="Sales by Day of Week")
            fig_dow.update_traces(textposition="outside")
            T(fig_dow, height=380, coloraxis_showscale=False,
              title_font=dict(size=14, color="#1a1a2e"),
              margin=dict(l=10,r=10,t=50,b=60))
            st.plotly_chart(fig_dow, use_container_width=True)

    with col2:
        if "MonthName" in df.columns and "GrossSales" in df.columns:
            mon_order = ["Jan","Feb","Mar","Apr","May","Jun",
                         "Jul","Aug","Sep","Oct","Nov","Dec"]
            mon = df.groupby("MonthName")["GrossSales"].sum().reindex(mon_order).reset_index()
            mon.columns = ["Month","Sales"]
            fig_mon = px.bar(mon, x="Month", y="Sales",
                             color="Sales", color_continuous_scale=ORANGE_SEQ,
                             text=mon["Sales"].apply(fmt),
                             title="Sales by Month (All Years)")
            fig_mon.update_traces(textposition="outside")
            T(fig_mon, height=380, coloraxis_showscale=False,
              title_font=dict(size=14, color="#1a1a2e"),
              margin=dict(l=10,r=10,t=50,b=40))
            st.plotly_chart(fig_mon, use_container_width=True)

    # Year over year monthly comparison
    if "Year" in df.columns and "Month" in df.columns and "GrossSales" in df.columns:
        st.markdown("### Year-over-Year Monthly Comparison")
        yoy = df.groupby(["Year","Month"])["GrossSales"].sum().reset_index()
        yoy["YearStr"] = yoy["Year"].astype(str)
        fig_yoy = px.line(yoy, x="Month", y="GrossSales", color="YearStr",
                          color_discrete_sequence=PALETTE,
                          markers=True, title="YoY Monthly Sales by Year",
                          line_shape="spline")
        fig_yoy.update_traces(line=dict(width=2.5), marker=dict(size=6))
        fig_yoy.update_xaxes(tickvals=list(range(1,13)),
                              ticktext=["Jan","Feb","Mar","Apr","May","Jun",
                                        "Jul","Aug","Sep","Oct","Nov","Dec"])
        T(fig_yoy, height=400, title_font=dict(size=14, color="#1a1a2e"),
          legend=dict(orientation="h", y=1.08, title_text="Year"))
        st.plotly_chart(fig_yoy, use_container_width=True)

    # Customer × Sales scatter by week
    if "TrWeekEndDate" in df.columns:
        st.markdown("### Weekly Customer Count vs Revenue")
        weekly = df.groupby("TrWeekEndDate").agg(
            Sales=("GrossSales","sum"),
            Customers=("CustomerCount","sum"),
        ).reset_index()
        fig_sc = px.scatter(weekly, x="Customers", y="Sales",
                            trendline="ols",
                            color_discrete_sequence=["#ff6b00"],
                            hover_data={"TrWeekEndDate": True},
                            title="Customer Count vs Gross Sales (weekly, with trend)")
        fig_sc.update_traces(marker=dict(size=6, opacity=0.7))
        T(fig_sc, height=380, title_font=dict(size=14, color="#1a1a2e"))
        st.plotly_chart(fig_sc, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TAB 6 — DATA EXPLORER
# ════════════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown("### Data Explorer")

    with st.expander("📊 Summary Statistics", expanded=True):
        num_cols = df.select_dtypes(include="number").columns.tolist()
        if num_cols:
            st.dataframe(df[num_cols].describe().round(2), use_container_width=True)

    with st.expander("🏪 Store Summary Table", expanded=False):
        if "PCNumber" in df.columns:
            store_summary = df.groupby("PCNumber").agg(
                GrossSales=("GrossSales","sum"),
                NetSales=("NetSalesMinusTax","sum"),
                Customers=("CustomerCount","sum"),
                DunkinSales=("DunkinSales","sum"),
                BaskinSales=("BaskinSales","sum"),
                Rows=("GrossSales","count"),
            ).reset_index()
            store_summary["AvgCheck"] = (store_summary["GrossSales"] / store_summary["Customers"].replace(0,pd.NA)).round(2)
            for c in ["GrossSales","NetSales","DunkinSales","BaskinSales"]:
                store_summary[c] = store_summary[c].apply(fmt)
            st.dataframe(store_summary, use_container_width=True)

    st.markdown("### Full Data Table")
    st.dataframe(df.reset_index(drop=True), use_container_width=True, height=420)

    csv_out = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download Filtered Data as CSV", csv_out,
                       "dunkin_sales_filtered.csv", "text/csv")

st.markdown("")
st.caption("Dunkin' Multi-Store Sales Intelligence · PC 301798 · 343672 · 332860 · 2021–2024 · Streamlit & Plotly")
