
import streamlit as st
import pandas as pd
import pydeck as pdk
import visualization as vis

st.set_page_config(page_title="Customer Brand Mapper", layout="wide")
st.title("🗺️ Customer Locations by Brand (Color & Sales‑Scaled Size)")

st.markdown(
    """**CSV columns (header optional):**

1. Latitude  
2. Longitude  
3. Brand  
4. Sales  

* Pick custom colors per brand  
* Toggle point‑size scaling by sales  
* Set **per‑brand** min/max pixel size when scaling is enabled.""")

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

    brand_controls = {}
    default_palette = {b: vis._c(i) for i, b in enumerate(all_brands)}

    for b in selected:
        st.sidebar.markdown(f"### {b}")
        default_hex = "#{:02x}{:02x}{:02x}".format(*default_palette[b])
        color_hex = st.sidebar.color_picker("Color", default_hex, key=f"color_{b}")
        color_rgb = hex_to_rgb(color_hex)

        if scale_by_sales:
            min_px = st.sidebar.number_input("Min size (px)", min_value=0.5, max_value=50.0, value=4.0, step=0.5, key=f"min_{b}")
            max_px = st.sidebar.number_input("Max size (px)", min_value=min_px+0.5, max_value=100.0, value=20.0, step=0.5, key=f"max_{b}")
            brand_controls[b] = {"color": color_rgb, "min_px": min_px, "max_px": max_px}
        else:
            fixed_px = st.sidebar.number_input("Point size (px)", min_value=1.0, max_value=50.0, value=6.0, step=0.5, key=f"size_{b}")
            brand_controls[b] = {"color": color_rgb, "fixed_px": fixed_px}

    if selected:
        show_df = df[df["brand"].isin(selected)].copy()
        layers = []

        for idx, b in enumerate(selected):
            sub = show_df[show_df["brand"] == b].copy()
            if sub.empty:
                continue

            color = brand_controls[b]["color"]

            if scale_by_sales:
                min_px = brand_controls[b]["min_px"]
                max_px = brand_controls[b]["max_px"]
                s_min, s_max = sub["sales"].min(), sub["sales"].max()
                if pd.isna(s_min) or s_max == s_min:
                    sub["radius"] = (min_px + max_px) / 2.0
                else:
                    sub["radius"] = min_px + (sub["sales"] - s_min) / (s_max - s_min) * (max_px - min_px)

                layer = pdk.Layer(
                    "ScatterplotLayer",
                    sub,
                    get_position=["lon", "lat"],
                    get_fill_color=color,
                    get_line_color=color,
                    get_radius="radius",
                    radius_scale=1,
                    pickable=True,
                    opacity=0.85
                )
            else:
                px = brand_controls[b]["fixed_px"]
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

        centroid_lat = show_df["lat"].mean()
        centroid_lon = show_df["lon"].mean()

        deck = vis._build_deck(layers)
        deck.initial_view_state.latitude = float(centroid_lat)
        deck.initial_view_state.longitude = float(centroid_lon)
        deck.initial_view_state.zoom = 3.5

        st.pydeck_chart(deck)
        st.success(f"Rendered {len(show_df):,} points across {len(selected)} brand(s).")
    else:
        st.info("No brands selected.")
