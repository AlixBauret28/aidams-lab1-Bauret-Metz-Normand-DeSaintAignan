# Import streamlit and other necessary libraries
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Set page configuration
st.set_page_config(page_title="Global Steel Plants Dashboard", page_icon="🏭", layout="wide")

CAP = "Nominal crude steel capacity (ttpa)"


@st.cache_data
def load_data():
    plants = pd.read_csv("data/plants_clean.csv")
    exposure = pd.read_csv("data/plants_with_exposure.csv")
    companies = pd.read_csv("data/company_agg.csv")
    return plants, exposure, companies


plants, exposure, companies = load_data()

# Title and description
st.title("🏭 Global Steel Plants & Climate Exposure")
st.markdown(
    "Explore steel plants worldwide (Global Energy Monitor) and the economic exposure "
    "around them (LitPop, China / India / Japan)."
)

# Sidebar for filters
st.sidebar.header("Filters")

# - Region/country filter
regions = st.sidebar.multiselect("Region", sorted(plants["Region"].dropna().unique()))
countries_list = plants[plants["Region"].isin(regions)] if regions else plants
countries = st.sidebar.multiselect("Country/area", sorted(countries_list["Country/area"].dropna().unique()))

# - Company selector
companies_sel = st.sidebar.multiselect("Company (Owner)", sorted(plants["Owner"].dropna().unique()))

# - Capacity range slider
max_cap = int(plants[CAP].max())
cap_range = st.sidebar.slider("Crude steel capacity (ttpa)", 0, max_cap, (0, max_cap))

# Apply filters
filtered = plants.copy()
if regions:
    filtered = filtered[filtered["Region"].isin(regions)]
if countries:
    filtered = filtered[filtered["Country/area"].isin(countries)]
if companies_sel:
    filtered = filtered[filtered["Owner"].isin(companies_sel)]
filtered = filtered[filtered[CAP].fillna(0).between(*cap_range)]

# Main content area
# - KPI metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Plants", f"{len(filtered):,}")
col2.metric("Total capacity", f"{filtered[CAP].sum() / 1000:,.0f} Mt/yr")
col3.metric("Companies", f"{filtered['Owner'].nunique():,}")
col4.metric("Countries", f"{filtered['Country/area'].nunique():,}")

# - Interactive map
tab1, tab2, tab3 = st.tabs(["Plant map", "LitPop exposure", "Companies"])

with tab1:
    fig = px.scatter_geo(
        filtered.assign(size=filtered[CAP].fillna(0).clip(lower=1)),
        lat="Latitude", lon="Longitude",
        color="Region", size="size", size_max=20,
        hover_name="Plant name (English)",
        hover_data={"Owner": True, "Country/area": True, CAP: ":,.0f",
                    "size": False, "Latitude": False, "Longitude": False},
        projection="natural earth",
    )
    fig.update_layout(height=550, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, width="stretch")

with tab2:
    exp = exposure[exposure["GEM plant ID"].isin(filtered["GEM plant ID"])].copy()
    if exp.empty:
        st.info("No LitPop data for this selection (only China, India and Japan are covered).")
    else:
        exp["log10_exposure"] = np.log10(exp["litpop_value_usd"].clip(lower=1))
        fig = px.scatter_geo(
            exp, lat="Latitude", lon="Longitude",
            color="log10_exposure", color_continuous_scale="Viridis",
            hover_name="Plant name (English)",
            hover_data={"Owner": True, "litpop_value_usd": ":,.0f",
                        "log10_exposure": False, "Latitude": False, "Longitude": False},
        )
        fig.update_geos(fitbounds="locations")
        fig.update_layout(height=550, margin=dict(l=0, r=0, t=10, b=0),
                          coloraxis_colorbar_title="log10 USD")
        st.plotly_chart(fig, width="stretch")

with tab3:
    comp = companies[companies["Owner"].isin(filtered["Owner"])]
    top = comp.sort_values("total_capacity", ascending=False).head(15)
    fig = px.bar(top, x="total_capacity", y="Owner", orientation="h",
                 title="Top 15 companies by capacity (ttpa)")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=500)
    st.plotly_chart(fig, width="stretch")

# - Data table
st.subheader("Plant data")
st.dataframe(
    filtered[["Plant name (English)", "Owner", "Country/area", "Region", CAP, "Plant age"]],
    width="stretch", hide_index=True,
)

# Footer with data sources and notes
st.markdown("---")
st.caption(
    "Sources: Global Energy Monitor – Global Iron and Steel Tracker (June 2026); "
    "LitPop produced-capital exposure, ETH Zurich (300 arcsec). "
    "Capacity = nominal crude steel capacity, all statuses. "
    "LitPop exposure only available for China, India and Japan. "
    "AIDAMS Lab 1 – Bauret, Metz, Normand."
)
