
import streamlit as st
import pandas as pd
import pydeck as pdk
import visualization as vis

st.set_page_config(page_title="Customer Brand Mapper", layout="wide")
st.title("🗺️ Customer Locations by Brand (Enhanced Sales Scaling)")

st.markdown(
    """CSV columns (header optional):

1. Latitude  
2. Longitude  
3. Brand  
4. Sales  

* Choose colors per brand  
* Toggle per‑brand min/max pixel sizes when scaling by sales  
* Scaling now uses **pixel units** so points remain visible at any zoom""")

file = st.file_uploader("Upload CSV", type=["csv"])

@st.cache_data(show_spinner=False)
def load_df(f):
    df = pd.read_csv(f, header=None).iloc[:, :4]
    df.columns = ["lat", "lon", "brand", "sales"]
    df.dropna(subset=["lat", "lon", "brand"], inplace=True)
    df["brand"] = df["brand"].astype(str)
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
    return df

def hex_to_rgb(h):
    h = h.lstrip("#")
    return [int(h[i:i+2], 16) for i in (0, 2, 4)]

if file is not None:
    df = load_df(file)
    all_brands = sorted(df["brand"].unique())

    st.sidebar.header("Display Settings")
    selected = st.sidebar.multiselect("Brands to show:", all_brands, default=all_brands)

    scale_by_sales = st.sidebar.checkbox("Scale point size by sales", value=False)

    brand_cfg = {}
    default_palette = {b: vis._c(i) for i, b in enumerate(all_brands)}

    for b in selected:
        st.sidebar.markdown(f"### {b}")
        default_hex = "#{:02x}{:02x}{:02x}".format(*default_palette[b])
        color_hex = st.sidebar.color_picker("Color", default_hex, key=f"color_{b}")
        color_rgb = hex_to_rgb(color_hex)

        if scale_by_sales:
            min_px = st.sidebar.number_input("Min px", 0.5, 50.0, 4.0, 0.5, key=f"min_{b}")
            max_px = st.sidebar.number_input("Max px", min_px+0.5, 100.0, 20.0, 0.5, key=f"max_{b}")
            brand_cfg[b] = {"color": color_rgb, "min_px": min_px, "max_px": max_px}
        else:
            fixed_px = st.sidebar.number_input("Point px", 1.0, 50.0, 6.0, 0.5, key=f"size_{b}")
            brand_cfg[b] = {"color": color_rgb, "fixed_px": fixed_px}

    if selected:
        show = df[df["brand"].isin(selected)].copy()
        layers = []

        for b in selected:
            sub = show[show["brand"] == b].copy()
            if sub.empty:
                continue
            color = brand_cfg[b]["color"]

            if scale_by_sales:
                min_px = brand_cfg[b]["min_px"]
                max_px = brand_cfg[b]["max_px"]
                smin, smax = sub["sales"].min(), sub["sales"].max()
                if pd.isna(smin) or smax == smin:
                    sub["radius"] = (min_px + max_px) / 2.0
                else:
                    sub["radius"] = min_px + (sub["sales"] - smin) / (smax - smin) * (max_px - min_px)

                layer = pdk.Layer(
                    "ScatterplotLayer",
                    sub,
                    get_position=["lon", "lat"],
                    get_fill_color=color,
                    get_line_color=color,
                    get_radius="radius",
                    radius_units="pixels",  # ensure radius interpreted as pixels
                    pickable=True,
                    opacity=0.85
                )
            else:
                px = brand_cfg[b]["fixed_px"]
                layer = pdk.Layer(
                    "ScatterplotLayer",
                    sub,
                    get_position=["lon", "lat"],
                    get_fill_color=color,
                    get_line_color=color,
                    radius_min_pixels=px,
                    pickable=True,
                    opacity=0.85
                )
            layers.append(layer)

        view_state = pdk.ViewState(
            latitude=float(show["lat"].mean()),
            longitude=float(show["lon"].mean()),
            zoom=3.5
        )

        deck = vis._build_deck(layers)
        deck.initial_view_state = view_state

        st.pydeck_chart(deck)
        st.success(f"{len(show):,} points displayed across {len(selected)} brands.")
    else:
        st.info("No brands selected.")
