import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Global CO₂ Emissions Dashboard",
    page_icon="🌍",
    layout="wide"
)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("data/owid-co2-data.csv")
    df = df[df["year"] >= 1950]
    df = df.loc[:, df.isna().mean() < 0.70]
    df = df[df["iso_code"].notna()]
    return df

df = load_data()

# ── HEADER ────────────────────────────────────────────────────────────────────
st.title("🌍 Global CO₂ Emissions Explorer")
st.markdown("**Analyze, compare, and explore CO₂ emissions across countries, fuels, and time.**")
st.markdown("---")

# ── SIDEBAR FILTERS ───────────────────────────────────────────────────────────
st.sidebar.header("🔧 Filters")

year_range = st.sidebar.slider(
    "Select Year Range",
    min_value=int(df["year"].min()),
    max_value=int(df["year"].max()),
    value=(1990, 2023)
)

all_countries = sorted(df["country"].unique().tolist())

g7 = ["Canada", "France", "Germany", "Italy", "Japan", "United Kingdom", "United States"]
selected_countries = st.sidebar.multiselect(
    "Select Countries (for comparison charts)",
    options=all_countries,
    default=g7
)

top_n = st.sidebar.slider("Top N Countries to Show", min_value=5, max_value=20, value=10)

# ── KPI METRICS ───────────────────────────────────────────────────────────────
latest_year = df["year"].max()
latest = df[df["year"] == latest_year]

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_co2 = df[df["year"] == latest_year]["co2"].sum()
    st.metric("🌐 Global CO₂ (Latest Year)", f"{total_co2:,.0f} Mt")

with col2:
    top_emitter = latest.sort_values("co2", ascending=False).iloc[0]["country"]
    st.metric("🏭 Biggest Emitter", top_emitter)

with col3:
    avg_per_capita = latest["co2_per_capita"].mean()
    st.metric("👤 Avg CO₂ per Capita", f"{avg_per_capita:.2f} t")

with col4:
    year_min, year_max = year_range
    st.metric("📅 Year Range Selected", f"{year_min} – {year_max}")

st.markdown("---")

# ── CHART 1: TOP N EMITTERS ───────────────────────────────────────────────────
st.subheader(f"📊 Q1 — Top {top_n} CO₂ Emitting Countries ({latest_year})")

top_emitters = (
    df[df["year"] == latest_year]
    .groupby("country")["co2"]
    .sum()
    .sort_values(ascending=False)
    .head(top_n)
    .reset_index()
)

fig1 = px.bar(
    top_emitters,
    x="co2",
    y="country",
    orientation="h",
    title=f"China and USA Dominate Global CO₂ Emissions in {latest_year}",
    labels={"co2": "CO₂ Emissions (Million Tonnes)", "country": "Country"},
    template="plotly_white",
    color="co2",
    color_continuous_scale="Oranges",
    text="co2"
)
fig1.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
fig1.update_yaxes(autorange="reversed")
fig1.update_layout(coloraxis_showscale=False, showlegend=False)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("---")

# ── CHART 2: GLOBAL TREND ─────────────────────────────────────────────────────
st.subheader("📈 Q3 — Global CO₂ Emissions Trend")

filtered_global = (
    df[(df["year"] >= year_min) & (df["year"] <= year_max)]
    .groupby("year")["co2"]
    .sum()
    .reset_index()
)

fig3 = px.line(
    filtered_global,
    x="year",
    y="co2",
    title=f"Global CO₂ Emissions Rose Sharply Between {year_min} and {year_max}",
    labels={"co2": "CO₂ Emissions (Million Tonnes)", "year": "Year"},
    template="plotly_white",
    color_discrete_sequence=["#E25822"]
)
fig3.update_traces(line_width=2.5)
fig3.update_layout(showlegend=False)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# ── CHART 3: COUNTRY COMPARISON ───────────────────────────────────────────────
st.subheader("🌐 Q7 — Country CO₂ Comparison Over Time")

if selected_countries:
    filtered_countries = df[
        (df["country"].isin(selected_countries)) &
        (df["year"] >= year_min) &
        (df["year"] <= year_max)
    ]

    fig7 = px.line(
        filtered_countries,
        x="year",
        y="co2",
        color="country",
        title="G7 Countries Have Mostly Reduced Emissions Since 2000",
        labels={"co2": "CO₂ Emissions (Million Tonnes)", "year": "Year"},
        template="plotly_white"
    )
    fig7.update_traces(line_width=2)
    st.plotly_chart(fig7, use_container_width=True)
else:
    st.warning("Please select at least one country from the sidebar.")

st.markdown("---")

# ── CHART 4: FUEL TYPE BREAKDOWN ──────────────────────────────────────────────
st.subheader("⛽ Q8 — CO₂ by Fuel Type Since 1990")

fuel_data = (
    df[(df["year"] >= year_min) & (df["year"] <= year_max)]
    .groupby("year")[["coal_co2", "oil_co2", "gas_co2"]]
    .sum()
    .reset_index()
)

fuel_melted = fuel_data.melt(
    id_vars="year",
    var_name="Fuel Type",
    value_name="CO₂ Emissions"
)

fuel_melted["Fuel Type"] = fuel_melted["Fuel Type"].map({
    "coal_co2": "Coal",
    "oil_co2": "Oil",
    "gas_co2": "Gas"
})

fig8 = px.line(
    fuel_melted,
    x="year",
    y="CO₂ Emissions",
    color="Fuel Type",
    title="Coal Remains the Biggest CO₂ Source Despite Recent Plateau",
    labels={"CO₂ Emissions": "CO₂ (Million Tonnes)", "year": "Year"},
    template="plotly_white",
    color_discrete_map={"Coal": "#333333", "Oil": "#E25822", "Gas": "#4C8BE2"}
)
fig8.update_traces(line_width=2.5)
st.plotly_chart(fig8, use_container_width=True)

st.markdown("---")

# ── CHART 5: GDP vs CO₂ SCATTER ──────────────────────────────────────────────
st.subheader("💰 Q6 — GDP vs CO₂ Emissions (Latest Available Year)")

scatter_data = df[df["year"] == 2022][["country", "gdp", "co2", "co2_per_capita"]].dropna()

fig6 = px.scatter(
    scatter_data,
    x="gdp",
    y="co2",
    hover_name="country",
    size="co2_per_capita",
    title="Richer Countries Emit More CO₂ — But Efficiency Varies Widely",
    labels={
        "gdp": "GDP (International $)",
        "co2": "CO₂ Emissions (Million Tonnes)",
        "co2_per_capita": "CO₂ per Capita"
    },
    template="plotly_white",
    color="co2_per_capita",
    color_continuous_scale="RdYlGn_r"
)
fig6.update_traces(marker=dict(opacity=0.7))
st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style='text-align: center; color: grey; font-size: 12px;'>
    Data source: Our World in Data — CO₂ and Greenhouse Gas Emissions Dataset<br>
    Built with Python, Plotly & Streamlit | Abhishek Lohani | MSc Data Science 2026
    </div>
    """,
    unsafe_allow_html=True
)
