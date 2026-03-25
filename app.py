import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

st.set_page_config(
    page_title="YouTube Top Creators Dashboard",
    page_icon="▶️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #0f0f0f; }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #ff0000;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .stMetric label { color: #aaaaaa !important; font-size: 13px !important; }
    .stMetric [data-testid="stMetricValue"] { color: #ff4444 !important; font-size: 26px !important; font-weight: 700; }
    h1, h2, h3 { color: #ffffff !important; }
    .section-header {
        color: #ff0000;
        font-size: 20px;
        font-weight: 700;
        margin-top: 10px;
        border-bottom: 2px solid #ff0000;
        padding-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("youtube_data.csv")
    df["created_year"] = pd.to_numeric(df["created_year"], errors="coerce")
    df["subscribers_M"] = df["subscribers"] / 1e6
    df["video_views_B"] = df["video views"] / 1e9
    df["earnings_yearly_avg"] = (df["highest_yearly_earnings"] + df["lowest_yearly_earnings"]) / 2
    return df

df = load_data()

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg", width=160)
    st.markdown("## 🎛️ Filters")

    all_categories = sorted(df["category"].dropna().unique())
    selected_cats = st.multiselect("Category", all_categories, default=all_categories[:5])

    all_countries = sorted(df["Country"].dropna().unique())
    selected_countries = st.multiselect("Country", all_countries, default=["United States", "India", "Brazil"])

    year_min = int(df["created_year"].min()) if df["created_year"].notna().any() else 2005
    year_max = int(df["created_year"].max())
    year_range = st.slider("Channel Created Year", year_min, year_max, (2006, 2020))

    top_n = st.slider("Top N Creators to Display", 5, 50, 20)

filtered = df.copy()
if selected_cats:
    filtered = filtered[filtered["category"].isin(selected_cats)]
if selected_countries:
    filtered = filtered[filtered["Country"].isin(selected_countries)]
filtered = filtered[
    (filtered["created_year"] >= year_range[0]) & (filtered["created_year"] <= year_range[1])
]

PLOT_BG = "rgba(15,15,15,0)"
PAPER_BG = "rgba(15,15,15,0)"
FONT_COLOR = "#dddddd"
GRID_COLOR = "#2a2a2a"
RED = "#ff0000"
PINK = "#ff4488"
BLUE = "#4488ff"

def dark_layout(fig, title=""):
    fig.update_layout(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PAPER_BG,
        font=dict(color=FONT_COLOR, size=12),
        title=dict(text=title, font=dict(color="#ffffff", size=16), x=0.01),
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0.4)", bordercolor="#333", borderwidth=1),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    )
    return fig

# ─── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("# ▶️ YouTube Top Creators — Global Dashboard")
st.markdown(f"*Showing **{len(filtered)}** of **{len(df)}** creators after filters*")

# ─── KPI METRICS ───────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("🎯 Creators", f"{len(filtered):,}")
c2.metric("👥 Total Subscribers", f"{filtered['subscribers'].sum()/1e9:.2f}B")
c3.metric("▶️ Total Views", f"{filtered['video views'].sum()/1e12:.2f}T")
c4.metric("💰 Avg Yearly Earnings", f"${filtered['earnings_yearly_avg'].mean()/1e6:.2f}M")
c5.metric("📹 Avg Uploads", f"{filtered['uploads'].mean():,.0f}")

st.markdown("---")

# ─── ROW 1 ─────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([1.5, 1])

with col1:
    st.markdown('<div class="section-header">🏆 Top Creators by Subscribers</div>', unsafe_allow_html=True)
    top = filtered.nlargest(top_n, "subscribers")[["Youtuber", "subscribers_M", "category", "Country"]].reset_index(drop=True)
    fig = px.bar(
        top, x="subscribers_M", y="Youtuber", orientation="h",
        color="category", text=top["subscribers_M"].round(1).astype(str) + "M",
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig.update_traces(textposition="outside", textfont_size=10)
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_layout(showlegend=True, height=420)
    dark_layout(fig)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown('<div class="section-header">📂 Subscribers by Category</div>', unsafe_allow_html=True)
    cat_subs = filtered.groupby("category")["subscribers_M"].sum().sort_values(ascending=False).reset_index()
    fig2 = px.pie(
        cat_subs, values="subscribers_M", names="category",
        color_discrete_sequence=px.colors.qualitative.Bold,
        hole=0.45,
    )
    fig2.update_traces(textposition="inside", textinfo="percent+label")
    fig2.update_layout(height=420, showlegend=False)
    dark_layout(fig2)
    st.plotly_chart(fig2, use_container_width=True)

# ─── ROW 2 ─────────────────────────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown('<div class="section-header">🌍 Channels by Country</div>', unsafe_allow_html=True)
    country_counts = filtered["Country"].value_counts().reset_index()
    country_counts.columns = ["Country", "count"]
    fig3 = px.choropleth(
        country_counts, locations="Country", locationmode="country names",
        color="count", color_continuous_scale="Reds",
        labels={"count": "Channels"},
    )
    fig3.update_layout(
        geo=dict(bgcolor="rgba(0,0,0,0)", showframe=False, showcoastlines=True,
                 coastlinecolor="#333", landcolor="#1a1a2e", showlakes=False),
        coloraxis_colorbar=dict(title="Channels", tickfont=dict(color=FONT_COLOR)),
        height=360,
    )
    dark_layout(fig3)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown('<div class="section-header">📅 Channel Creation Timeline</div>', unsafe_allow_html=True)
    year_counts = (
        filtered[filtered["created_year"].between(2005, 2022)]
        .groupby(["created_year", "category"])
        .size().reset_index(name="count")
    )
    fig4 = px.area(
        year_counts, x="created_year", y="count", color="category",
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig4.update_layout(height=360, xaxis_title="Year", yaxis_title="New Channels")
    dark_layout(fig4)
    st.plotly_chart(fig4, use_container_width=True)

# ─── ROW 3 ─────────────────────────────────────────────────────────────────────
col5, col6 = st.columns(2)

with col5:
    st.markdown('<div class="section-header">💸 Subscribers vs Earnings</div>', unsafe_allow_html=True)
    scatter_df = filtered.dropna(subset=["subscribers_M", "earnings_yearly_avg", "uploads"])
    fig5 = px.scatter(
        scatter_df, x="subscribers_M", y="earnings_yearly_avg",
        color="category", size="uploads", hover_name="Youtuber",
        size_max=30, log_y=True,
        color_discrete_sequence=px.colors.qualitative.Bold,
        labels={"subscribers_M": "Subscribers (M)", "earnings_yearly_avg": "Avg Yearly Earnings ($)"},
    )
    fig5.update_layout(height=380)
    dark_layout(fig5)
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    st.markdown('<div class="section-header">📊 Engagement Rate by Category</div>', unsafe_allow_html=True)
    eng = (
        filtered.groupby("category")["engagement_rate"]
        .agg(["mean", "median", "std"]).reset_index()
        .sort_values("mean", ascending=False)
    )
    fig6 = go.Figure()
    fig6.add_trace(go.Bar(
        x=eng["category"], y=eng["mean"], name="Mean",
        marker_color=RED, error_y=dict(type="data", array=eng["std"], visible=True)
    ))
    fig6.add_trace(go.Scatter(
        x=eng["category"], y=eng["median"], name="Median",
        mode="markers", marker=dict(color=BLUE, size=9, symbol="diamond")
    ))
    fig6.update_layout(height=380, xaxis_tickangle=-35, barmode="overlay")
    dark_layout(fig6)
    st.plotly_chart(fig6, use_container_width=True)

# ─── ROW 4 ─────────────────────────────────────────────────────────────────────
col7, col8 = st.columns([1, 1.2])

with col7:
    st.markdown('<div class="section-header">📈 Views per Upload vs Uploads</div>', unsafe_allow_html=True)
    vpu = filtered.dropna(subset=["uploads", "views_per_upload"])
    fig7 = px.scatter(
        vpu, x="uploads", y="views_per_upload", color="category",
        hover_name="Youtuber", log_x=True, log_y=True,
        color_discrete_sequence=px.colors.qualitative.Bold,
        labels={"uploads": "Total Uploads (log)", "views_per_upload": "Views per Upload (log)"},
    )
    fig7.update_layout(height=380)
    dark_layout(fig7)
    st.plotly_chart(fig7, use_container_width=True)

with col8:
    st.markdown('<div class="section-header">🔥 Top 10 by 30-Day Subscriber Growth</div>', unsafe_allow_html=True)
    top30 = filtered.nlargest(10, "subscribers_for_last_30_days")[
        ["Youtuber", "subscribers_for_last_30_days", "category"]
    ]
    fig8 = px.bar(
        top30, x="Youtuber", y="subscribers_for_last_30_days",
        color="category", text_auto=".2s",
        color_discrete_sequence=px.colors.qualitative.Bold,
        labels={"subscribers_for_last_30_days": "30-Day Sub Growth"},
    )
    fig8.update_traces(textposition="outside")
    fig8.update_layout(height=380, xaxis_tickangle=-30)
    dark_layout(fig8)
    st.plotly_chart(fig8, use_container_width=True)

# ─── DATA TABLE ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown('<div class="section-header">📋 Creator Data Table</div>', unsafe_allow_html=True)
show_cols = ["rank", "Youtuber", "Country", "category", "subscribers_M",
             "video_views_B", "uploads", "engagement_rate", "earnings_yearly_avg", "created_year"]
table_df = filtered[show_cols].rename(columns={
    "subscribers_M": "Subscribers (M)",
    "video_views_B": "Video Views (B)",
    "earnings_yearly_avg": "Avg Yearly Earnings ($)",
    "created_year": "Year Created",
    "engagement_rate": "Engagement Rate",
}).sort_values("rank").reset_index(drop=True)

st.dataframe(
    table_df.style.format({
        "Subscribers (M)": "{:.2f}",
        "Video Views (B)": "{:.2f}",
        "Avg Yearly Earnings ($)": "${:,.0f}",
        "Engagement Rate": "{:.4f}",
    }),
    use_container_width=True,
    height=350,
)

st.caption("Data source: YouTube Top Global Creators Dataset")
