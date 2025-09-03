import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
import requests

st.set_page_config(layout="wide")

# 🔑 Your OpenRouteService API key
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjJkMzg4NDMwZmFkODQ3NjM5NTg3NjU2NjI2YTQxYTZhIiwiaCI6Im11cm11cjY0In0="

# Load rooms
@st.cache_data
def load_rooms():
    return pd.read_excel("rooms.xlsx")

rooms = load_rooms()

st.title("MUT Campus Room Finder")

# Map style selector
map_style = st.selectbox(
    "🗺️ Choose Map Style:",
    ["Standard", "Terrain", "Light", "Dark", "Satellite"]
)

search_query = st.text_input("🔍 Search for a room by name:")
filtered_rooms = rooms
if search_query:
    filtered_rooms = filtered_rooms[
        filtered_rooms["room_name"].str.contains(search_query, case=False, na=False)
    ]

if not filtered_rooms.empty:
    room_choice = st.selectbox("Select a room:", filtered_rooms["room_name"].unique())
    room_row = filtered_rooms[filtered_rooms["room_name"] == room_choice].iloc[0]
    room_lat, room_lon = room_row["lat"], room_row["lon"]

    st.markdown(f"""
    <div style="padding:15px; background:#f9f9f9; border-radius:10px;">
        <h3>📍 {room_row['room_name']}</h3>
        <p>🏢 Building: <b>{room_row['building']}</b></p>
        <p>🛗 Floor: <b>{room_row['floor']}</b></p>
    </div>
    """, unsafe_allow_html=True)

    # Default campus center
    default_lat, default_lon = -0.748, 37.150

    # Get GPS
    user_coords = streamlit_js_eval(
        js_expressions="""
        new Promise((resolve) => {
            navigator.geolocation.getCurrentPosition(
                pos => resolve({lat: pos.coords.latitude, lon: pos.coords.longitude}),
                err => resolve(null)
            );
        })
        """,
        key="gps_live",
        default=None
    )

    if user_coords:
        user_lat, user_lon = user_coords["lat"], user_coords["lon"]
    else:
        user_lat, user_lon = default_lat, default_lon
        st.info("📍 GPS not available. Showing campus center.")

    # Map tiles
    tile_layers = {
        "Standard": "OpenStreetMap",
        "Terrain": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
        "Light": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png",
        "Dark": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}{r}.png",
        "Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    }

    m = folium.Map(
        location=[user_lat, user_lon],
        zoom_start=17,
        tiles=tile_layers[map_style],
        attr=""
    )

    # Markers
    folium.Marker([user_lat, user_lon], tooltip="You are here", icon=folium.Icon(color="blue")).add_to(m)
    folium.Marker([room_lat, room_lon], tooltip=room_choice, icon=folium.Icon(color="red")).add_to(m)

    # 🚶 ORS Walking Route
    try:
        url = "https://api.openrouteservice.org/v2/directions/foot-walking"
        headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
        body = {
            "coordinates": [
                [user_lon, user_lat],  # start
                [room_lon, room_lat]   # end
            ]
        }
        response = requests.post(url, json=body, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "features" in data and len(data["features"]) > 0:
            route = data["features"][0]["geometry"]
            distance = round(data["features"][0]["properties"]["segments"][0]["distance"]/1000, 2)
            duration = round(data["features"][0]["properties"]["segments"][0]["duration"]/60, 1)

            folium.GeoJson(route, style_function=lambda x: {"color": "green", "weight": 4}).add_to(m)
            st.success(f"🚶 Distance: **{distance} km** | ⏱ Time: **{duration} mins**")
        else:
            st.warning("⚠️ No walking route found.")

    except requests.exceptions.RequestException as e:
        st.error(f"⚠️ Could not fetch walking route: {e}")

    st_folium(m, width=750, height=520)

    # Footer credits
    st.markdown(
        """
        <div style="text-align:center; font-size:13px; color:#555; margin-top:5px;">
            🗺️ Map data © <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> | 
            Routes by <a href="https://openrouteservice.org/" target="_blank">OpenRouteService</a> | 
            Made by <b style="color:#e63946; background:yellow; padding:2px 6px; border-radius:5px;">MUT TECH CLUB</b>
        </div>
        """,
        unsafe_allow_html=True
    )

else:
    st.warning("⚠️ No rooms found. Try another search.")
