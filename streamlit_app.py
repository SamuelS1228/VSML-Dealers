
import streamlit as st
import pandas as pd
import pydeck as pdk
import visualization as vis

st.set_page_config(page_title="Customer Brand Mapper", layout="wide")
st.title("🗺️ Customer Locations by Brand")

st.markdown(
    """Upload a CSV with **three columns** (header optional):

1. Latitude  
2. Longitude  
3. Brand  

Use the sidebar to toggle which brands are displayed.  
The map uses the same styling and basemaps as the Warehouse Network Optimizer tool (Mapbox if available, otherwise free Carto).""")

file = st.file_uploader("Upload CSV", type=["csv"])

@st.cache_data(show_spinner=False)
def load_df(f):
    df = pd.read_csv(f, header=None).iloc[:, :3]
    df.columns = ["lat", "lon", "brand"]
    df.dropna(subset=["lat", "lon", "brand"], inplace=True)
    df["brand"] = df["brand"].astype(str)
    return df

if file is not None:
    df = load_df(file)
    brands_all = sorted(df["brand"].unique())
    chosen = st.sidebar.multiselect("Brands to display:", brands_all, default=brands_all)

    if chosen:
        show = df[df["brand"].isin(chosen)].copy()

        # build scatterplot layers (one per brand for legend clarity)
        layers = []
        for i, b in enumerate(brands_all):
            if b not in chosen:
                continue
            sub = show[show["brand"] == b]
            color = vis._c(i)  # reuse same palette
            sub["r"] = color[0]
            sub["g"] = color[1]
            sub["b"] = color[2]
            layer = pdk.Layer(
                "ScatterplotLayer",
                sub,
                get_position=["lon", "lat"],
                get_fill_color="[r,g,b]",
                get_line_color="[r,g,b]",
                radius_min_pixels=6,
                opacity=0.8,
                pickable=True,
            )
            layers.append(layer)

        # Center view
        view_state = pdk.ViewState(
            latitude=float(show["lat"].mean()),
            longitude=float(show["lon"].mean()),
            zoom=3.5
        )

        deck = vis._build_deck(layers)
        deck.initial_view_state = view_state  # override default center

        st.pydeck_chart(deck)
        st.success(f"Showing {len(show):,} customers across {len(chosen)} brand(s).")
    else:
        st.info("No brands selected.")
