import streamlit as st
import pandas as pd
from pathlib import Path
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(page_title="Campus Room Finder", page_icon="🧭", layout="centered")

st.title("🧭 Campus Room Finder (Free OSM + OSRM Directions)")
st.write("Search for a room and get real walking directions (powered by OpenStreetMap & OSRM).")

# --- DATA ---
DATA_PATH = Path("rooms.xlsx")

@st.cache_data
def load_rooms(path: Path):
    df = pd.read_excel(path)
    return df

if not DATA_PATH.exists():
    st.info("Upload your rooms.xlsx file (columns: room_id, room_name, building, floor, lat, lon).")
    up = st.file_uploader("Upload Excel", type=["xlsx"])
    if up:
        DATA_PATH.write_bytes(up.read())
        st.rerun()
    st.stop()

rooms = load_rooms(DATA_PATH)

# --- SEARCH ---
query = st.text_input("Search by room id, name, or building:", "")

filtered = rooms.copy()
if query.strip():
    q = query.lower()
    filtered = rooms[
        rooms["room_id"].str.lower().str.contains(q)
        | rooms["room_name"].str.lower().str.contains(q)
        | rooms["building"].str.lower().str.contains(q)
    ]

if filtered.empty:
    st.warning("No rooms found.")
    st.stop()

sel = st.selectbox(
    "Select a room",
    options=filtered.index,
    format_func=lambda i: f"{filtered.loc[i,'room_id']} • {filtered.loc[i,'room_name']} • {filtered.loc[i,'building']} (Floor {filtered.loc[i,'floor']})",
)

dest = filtered.loc[sel]
dest_lat, dest_lon = float(dest["lat"]), float(dest["lon"])

st.markdown(f"**Destination:** {dest['room_id']} — {dest['room_name']}<br>**Building:** {dest['building']} • **Floor:** {dest['floor']}", unsafe_allow_html=True)

# --- AUTO GET USER LOCATION ---
st.subheader("📍 Your Location")

location = st.empty()
js_code = """
<script>
navigator.geolocation.getCurrentPosition(
    (pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        const coords = lat + "," + lon;
        var streamlitDoc = window.parent.document;
        var coordInput = streamlitDoc.querySelector('input[data-testid="stTextInput"]');
        coordInput.value = coords;
        coordInput.dispatchEvent(new Event("input", { bubbles: true }));
    },
    (err) => {
        console.error(err);
    }
);
</script>
"""

coords = st.text_input("Auto coordinates", key="coords")  # hidden text input for JS to fill
st.components.v1.html(js_code, height=0, width=0)

has_coords = coords != ""
user_lat, user_lon = (0.0, 0.0)
if has_coords and "," in coords:
    try:
        user_lat, user_lon = map(float, coords.split(","))
        st.success(f"Detected location: {user_lat:.6f}, {user_lon:.6f}")
    except:
        has_coords = False

travel_mode = st.radio("Travel Mode", ["walking", "driving"], horizontal=True)

# --- MAP ---
m = folium.Map(location=[dest_lat, dest_lon], zoom_start=17)

# Destination marker
folium.Marker(
    [dest_lat, dest_lon],
    popup=f"{dest['room_id']} - {dest['room_name']}",
    tooltip="Destination",
    icon=folium.Icon(color="red", icon="flag")
).add_to(m)

if has_coords:
    # User marker
    folium.Marker(
        [user_lat, user_lon],
        popup="You are here",
        tooltip="Your location",
        icon=folium.Icon(color="blue", icon="user")
    ).add_to(m)

    # --- OSRM ROUTING ---
    osrm_url = f"http://router.project-osrm.org/route/v1/{travel_mode}/{user_lon},{user_lat};{dest_lon},{dest_lat}?overview=full&geometries=geojson"
    
    try:
        res = requests.get(osrm_url)
        data = res.json()
        if "routes" in data and len(data["routes"]) > 0:
            route = data["routes"][0]["geometry"]["coordinates"]
            route_latlon = [(lat, lon) for lon, lat in route]
            
            folium.PolyLine(
                locations=route_latlon,
                color="green",
                weight=4,
                opacity=0.8,
                tooltip=f"Route ({travel_mode})"
            ).add_to(m)
            
            distance = data["routes"][0]["distance"] / 1000
            duration = data["routes"][0]["duration"] / 60
            st.success(f"Route found: **{distance:.2f} km**, about **{duration:.1f} minutes** by {travel_mode}.")
        else:
            st.warning("No route found. Try another mode or location.")
    except Exception as e:
        st.error(f"Error fetching route from OSRM: {e}")

# Render map
st_map = st_folium(m, width=700, height=500)
