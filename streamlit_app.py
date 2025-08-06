
import streamlit as st
import pandas as pd
import pydeck as pdk
import visualization as vis

st.set_page_config(page_title="Customer Brand Mapper", layout="wide")
st.title("🗺️ Customer Locations by Brand (Resizable Points)")

st.markdown(
    """Upload a CSV with **three columns** (header optional):

1. Latitude  
2. Longitude  
3. Brand  

**New:** Use the sidebar sliders to control the point size for each brand individually.""")

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

    # Brand selection
    chosen = st.sidebar.multiselect("Brands to display:", brands_all, default=brands_all)

    # Define sliders for chosen brands
    size_settings = {}
    for b in chosen:
        size_settings[b] = st.sidebar.slider(
            f"{b} point size", min_value=2, max_value=20, value=6, step=1
        )

    if chosen:
        df_show = df[df["brand"].isin(chosen)].copy()
        layers = []

        for idx, b in enumerate(brands_all):
            if b not in chosen:
                continue
            sub = df_show[df_show["brand"] == b]
            if sub.empty:
                continue

            color = vis._c(idx)  # color palette from visualization.py
            size_px = size_settings[b]

            layer = pdk.Layer(
                "ScatterplotLayer",
                sub,
                get_position=["lon", "lat"],
                get_fill_color=color,
                radius_min_pixels=size_px,
                pickable=True,
                opacity=0.85
            )
            layers.append(layer)

        view_state = pdk.ViewState(
            latitude=float(df_show["lat"].mean()),
            longitude=float(df_show["lon"].mean()),
            zoom=3.5
        )

        deck = vis._build_deck(layers)
        deck.initial_view_state = view_state

        st.pydeck_chart(deck)
        st.success(
            f"Displaying {len(df_show):,} customers across "
            f"{len(chosen)} brand(s) with adjustable sizes."
        )
    else:
        st.info("No brands selected.")
