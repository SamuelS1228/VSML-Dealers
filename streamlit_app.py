
import streamlit as st
import pandas as pd
import pydeck as pdk
import visualization as vis
import re

st.set_page_config(page_title="Customer Brand Mapper", layout="wide")
st.title("🗺️ Customer Locations by Brand (Color & Size Controls)")

st.markdown(
    """**CSV columns (header optional):**

1. Latitude  
2. Longitude  
3. Brand  
4. Sales  

*Choose the brands to display in the sidebar.*  
*Pick custom colors for each brand.*  
*Optionally scale point sizes by sales.*""")

file = st.file_uploader("Upload CSV", type=["csv"])

@st.cache_data(show_spinner=False)
def load_df(f):
    df = pd.read_csv(f, header=None).iloc[:, :4]
    df.columns = ["lat", "lon", "brand", "sales"]
    df.dropna(subset=["lat", "lon", "brand"], inplace=True)
    df["brand"] = df["brand"].astype(str)
    # ensure numeric sales
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
    return df

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]

if file is not None:
    df = load_df(file)
    all_brands = sorted(df["brand"].unique())

    selected = st.sidebar.multiselect("Brands to display:", all_brands, default=all_brands)

    scale_by_sales = st.sidebar.checkbox("Scale point size by sales", value=False)

    # Default palette from visualization module
    default_palette = {b: vis._c(i) for i, b in enumerate(all_brands)}

    # Sidebar controls for brands
    brand_settings = {}
    for b in selected:
        st.sidebar.markdown(f"**{b}**")
        color_hex = "#{:02x}{:02x}{:02x}".format(*default_palette[b])
        chosen_color = st.sidebar.color_picker("Color", color_hex, key=f"color_{b}")
        if not scale_by_sales:
            size_px = st.sidebar.slider("Point size (px)", 2, 20, 6, key=f"size_{b}")
        else:
            size_px = None
        brand_settings[b] = {"color": hex_to_rgb(chosen_color), "size_px": size_px}

    if selected:
        show_df = df[df["brand"].isin(selected)].copy()

        layers = []
        sales_min, sales_max = show_df["sales"].min(), show_df["sales"].max()
        min_px, max_px = 4, 20  # for scaling
        if scale_by_sales and pd.notna(sales_min) and sales_max != sales_min:
            show_df["size"] = ((show_df["sales"] - sales_min) / (sales_max - sales_min)) * (max_px - min_px) + min_px
        else:
            show_df["size"] = None  # will be overwritten for non-scaled

        for idx, b in enumerate(all_brands):
            if b not in selected:
                continue
            sub = show_df[show_df["brand"] == b].copy()
            if sub.empty:
                continue
            color = brand_settings[b]["color"]
            if scale_by_sales and sub["size"].notna().any():
                layer = pdk.Layer(
                    "ScatterplotLayer",
                    sub,
                    get_position=["lon", "lat"],
                    get_fill_color=color,
                    get_line_color=color,
                    get_radius="size",
                    radius_scale=1,
                    radius_min_pixels=min_px,
                    radius_max_pixels=max_px,
                    pickable=True,
                    opacity=0.85
                )
            else:
                size_px = brand_settings[b]["size_px"] or 6
                layer = pdk.Layer(
                    "ScatterplotLayer",
                    sub,
                    get_position=["lon", "lat"],
                    get_fill_color=color,
                    get_line_color=color,
                    radius_min_pixels=size_px,
                    pickable=True,
                    opacity=0.85
                )
            layers.append(layer)

        view_state = pdk.ViewState(
            latitude=float(show_df["lat"].mean()),
            longitude=float(show_df["lon"].mean()),
            zoom=3.5
        )

        deck = vis._build_deck(layers)
        deck.initial_view_state = view_state

        st.pydeck_chart(deck)
        st.success(f"Displayed {len(show_df):,} points across {len(selected)} brand(s).")
    else:
        st.info("No brands selected.")
