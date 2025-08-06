
import streamlit as st
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="Customer Brand Mapper", layout="wide")
st.title("🗺️ Customer Locations by Brand")

st.markdown(
    """**CSV format (three columns):**

    1. Latitude  
    2. Longitude  
    3. Brand  

    Header row is optional. Use the sidebar to toggle brands.""")

file = st.file_uploader("Upload CSV", type=["csv"])

@st.cache_data(show_spinner=False)
def load_df(f):
    df = pd.read_csv(f, header=None).iloc[:, :3]
    df.columns = ["lat", "lon", "brand"]
    df.dropna(subset=["lat", "lon", "brand"], inplace=True)
    df["brand"] = df["brand"].astype(str)
    return df

if file is not None:
    data = load_df(file)
    unique_brands = sorted(data["brand"].unique())
    chosen = st.sidebar.multiselect("Brands to display:", unique_brands, default=unique_brands)

    if chosen:
        df_show = data[data["brand"].isin(chosen)].copy()

        # assign colors
        palette = [
            [31,119,180],[255,127,14],[44,160,44],
            [214,39,40],[148,103,189],[140,86,75],
            [227,119,194],[127,127,127],[188,189,34],[23,190,207]
        ]
        color_map = {b: palette[i % len(palette)] for i, b in enumerate(unique_brands)}
        df_show["color"] = df_show["brand"].map(color_map)

        layer = pdk.Layer(
            "ScatterplotLayer",
            df_show,
            get_position=["lon","lat"],
            get_fill_color="color",
            get_line_color="color",
            radius_min_pixels=5,
            pickable=True
        )

        view = pdk.ViewState(
            latitude=df_show["lat"].mean(),
            longitude=df_show["lon"].mean(),
            zoom=3.5
        )

        st.pydeck_chart(
            pdk.Deck(
                layers=[layer],
                initial_view_state=view,
                tooltip={"html":"<b>Brand:</b> {brand}<br><b>Lat:</b> {lat}<br><b>Lon:</b> {lon}"}
            )
        )
        st.success(f"Showing {len(df_show):,} customers across {len(chosen)} selected brand(s).")
    else:
        st.info("No brands selected.")
