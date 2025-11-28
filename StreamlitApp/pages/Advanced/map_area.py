from tools.widgets import render_time_selector
from tools.utils import (get_elhub_data, get_area_means)
import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import pandas as pd
from shapely.geometry import shape, Point
from datetime import datetime


def run():

    # --------------------- page title & time controls ---------------------
    st.markdown(f"### 🗺️ Electricity Production & Consumption Map")

    aggregation, start_dt, end_dt = render_time_selector()

    # Initialize data cache in session state
    if "data_cache" not in st.session_state:
        st.session_state.data_cache = {}

    def make_time_key(start, end):
        return f"{start.strftime('%Y%m%d')}_{end.strftime('%Y%m%d')}"

    # --------------------- Load data ---------------------

    time_key = make_time_key(start_dt, end_dt)

    if time_key in st.session_state.data_cache:
        df_prod, df_cons = st.session_state.data_cache[time_key]
        st.info(f"Using cached data for {start_dt.date()} → {end_dt.date()}")
    else:
        with st.spinner(f"Fetching data {start_dt.date()} → {end_dt.date()} from MongoDB..."):
            df_prod, df_cons = get_elhub_data(start_dt, end_dt)
            st.session_state.data_cache[time_key] = (df_prod, df_cons)
        st.success(f"Data loaded & cached for {start_dt.date()} → {end_dt.date()}")


    # If no data → stop
    if (df_prod is None or df_prod.empty) and (df_cons is None or df_cons.empty):
        st.error("No data found for the selected period.")
        st.stop()

    # page filters: mode + group
    st.markdown(f"#### ⛽ Energy Mode & Groups")

    # --- 3 columns layout for filters ---
    col1, col2 = st.columns([1, 1])

    if "mode" not in st.session_state:
        st.session_state.mode = "Production"

    if "group" not in st.session_state:
        st.session_state.group = "solar"

    # Data mode: Production / Consumption
    with col1:
        mode = st.selectbox("Data Type", ["Production", "Consumption"], key="mode")

    # Select correct group list based on mode
    if mode == "Production":
        groups = sorted(df_prod["productiongroup"].dropna().unique())
    else:
        groups = sorted(df_cons["consumptiongroup"].dropna().unique())

    with col2:
        group = st.selectbox("Group", groups, key="group")


    # --------------------- Load GeoJSON --------------------- 
    @st.cache_resource
    def load_geojson():
        with open("data/area.geojson") as f:
            return json.load(f)

    geojson_data = load_geojson()

    # --------------------- Build ID to Name Mapping ---------------------
    @st.cache_resource
    def build_id_to_name(gj):
        out = {}
        for f in gj.get("features", []):
            fid = f.get("id") or (f.get("properties") or {}).get("id")
            if fid is None:
                continue
            raw_name = (f.get("properties") or {}).get("ElSpotOmr")
            if raw_name:
                # remove spaces e.g. "NO 2" → "NO2"
                clean_name = raw_name.replace(" ", "")
                out[fid] = clean_name
        return out

    id_to_name = build_id_to_name(geojson_data)
    name_to_id = {name: fid for fid, name in id_to_name.items()}


    # --------------------- Build polygons for click detection ---------------------
    # Build shapely polygons once (session cache)
    if "polygons" not in st.session_state:
        polys = []
        for feat in geojson_data.get("features", []):
            fid = feat.get("id") or (feat.get("properties") or {}).get("id")
            if not fid:
                continue
            try:
                geom = shape(feat["geometry"])
            except Exception:
                continue
            polys.append((fid, geom))
        st.session_state.polygons = polys

    # Function to find feature ID given lon/lat
    def find_feature_id(lon: float, lat: float):
        if shape is None or "polygons" not in st.session_state:
            return None
        pt = Point(lon, lat)  # shapely uses (x,y) = (lon,lat)
        for fid, geom in st.session_state.polygons:
            if geom.covers(pt):  # boundary-inclusive
                return fid
        return None

    df = df_prod if mode == "Production" else df_cons

    # --------------------- Compute mean values per area ---------------------
    df_map = get_area_means(df, mode, group, start_dt, end_dt, aggregation)
    df_map["fid"] = df_map["area"].map(name_to_id)
    df_map = df_map.dropna(subset=["fid"]).copy()
    # Build value map for info box
    value_map = dict(zip(df_map["area"], df_map["value"]))

    # --------------------- Session state init ---------------------
    if "last_pin" not in st.session_state:
        st.session_state.last_pin = [59.9127, 10.7461]
    if "selected_feature_id" not in st.session_state:
        st.session_state.selected_feature_id = None

    # Preselect area for the initial pin (no click required)
    if st.session_state.selected_feature_id is None:
        lat, lon = st.session_state.last_pin
        st.session_state.selected_feature_id = find_feature_id(lon, lat)

    # Layout: map left, info right
    map_col, info_col = st.columns([2.2, 1])
    # 1. Inject mean values into geojson
    mean_dict = dict(zip(df_map["area"], df_map["value"]))  # formatted GWh/MWh/kWh

    for feature in geojson_data["features"]:
        # Clean "NO 2" → "NO2"
        raw = feature["properties"].get("ElSpotOmr", "")
        clean = raw.replace(" ", "")       # 💡 remove the space
        
        feature["properties"]["MeanValue"] = mean_dict.get(clean, "n/a")

    with map_col:

        m = folium.Map(location=st.session_state.last_pin, zoom_start=5)
        # 1. Choropleth layer
        folium.Choropleth(
            geo_data=geojson_data,
            data=df_map,
            columns=["fid", "value_raw"],
            key_on="feature.id",
            fill_color="YlOrRd",
            fill_opacity=0.5,
            line_opacity=0.8,
            line_color="white",
            highlight=True
        ).add_to(m)
        # 2. Tooltip layer (hover text)
        folium.GeoJson(
            geojson_data,
            name="Labels",
            tooltip=folium.features.GeoJsonTooltip(
                fields=["ElSpotOmr", "MeanValue"],
                aliases=["Price Area:", "Mean value:"],
                sticky=True,
                localize=True,
                labels=True,
                style="""
                    background-color: white;
                    border: 1px solid black;
                    border-radius: 3px;
                    padding: 5px;
                """
            ),
            highlight_function=lambda f: {
                "weight": 3,
                "color": "black",
                "fillOpacity": 0
            }
        ).add_to(m)

        # Single pin (last clicked)
        folium.Marker(
            location=st.session_state.last_pin,
            icon=folium.Icon(color="red"),
            popup=f"{st.session_state.last_pin[0]:.5f}, {st.session_state.last_pin[1]:.5f}"
        ).add_to(m)

        # Render (width inherits from column)
        out = st_folium(m, key="choropleth_map", height=600, width=None)

        # Process click: update pin and polygon ID, then single rerun
        if out and out.get("last_clicked"):
            lat = out["last_clicked"]["lat"]
            lon = out["last_clicked"]["lng"]
            new_coord = [lat, lon]

            if new_coord != st.session_state.last_pin:
                st.session_state.last_pin = new_coord
                fid = find_feature_id(lon, lat)
                st.session_state.selected_feature_id = fid
                st.write(fid)
                # Update selected area name
                if fid is None:
                    st.session_state.selected_area_name = None
                else:
                    st.session_state.selected_area_name = id_to_name.get(fid, None)

                st.rerun()

    # --------------------- Info box ---------------------
    with info_col:
        st.subheader("📍 Selected Price Area")
        st.write(f"Lat: {st.session_state.last_pin[0]:.6f}")
        st.write(f"Lon: {st.session_state.last_pin[1]:.6f}")

        if st.session_state.selected_feature_id is None:
            st.write("Outside known features.")
        else:
            fid = st.session_state.selected_feature_id
            area_name = id_to_name.get(fid, f"ID {fid}")
            val = value_map.get(area_name, "n/a")
            st.write(f"Area: {area_name}")
            st.write(f"Mean Value: {val}")
        
        st.subheader("📊 Mean values per price area")

        # Sorting should use numeric value_raw, not formatted string
        df_show = df_map[["area", "value_raw", "value"]].copy()
        df_show = df_show.sort_values(by="value_raw", ascending=False)

        # Show only area & formatted text
        df_show = df_show[["area", "value"]]

        st.data_editor(
            df_show,
            hide_index=True,
            column_config={
                "area": st.column_config.TextColumn(
                    "Price Area",
                    width="small",
                ),
                "value": st.column_config.TextColumn(
                    "Mean Value",
                    width="medium",
                ),
            },
        )
        # Add expandable section with unit explanation
        with st.expander("ℹ️ Unit Explanation"):
            st.markdown("""
            **All energy values are originally measured in kWh.**

            For readability, the dashboard automatically converts values to:
            - **kWh** for values below 1,000  
            - **MWh** for values in the thousands (× 1,000)  
            - **GWh** for values in the millions (× 1,000,000)

            Map colors always use the raw numerical values (in **kWh**),  
            while tooltips and tables display the converted units for clarity.
                """)

