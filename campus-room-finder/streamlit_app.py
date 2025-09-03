import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
import requests
from math import radians, sin, cos, sqrt, atan2

st.set_page_config(layout="wide")

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

    # Pick tile layer
    tile_layers = {
        "Standard": "OpenStreetMap",
        "Terrain": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
        "Light": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png",
        "Dark": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}{r}.png",
        "Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    }

    # Build map
    m = folium.Map(location=[user_lat, user_lon], zoom_start=17,
                   tiles=tile_layers[map_style], attr="")

    # Markers
    folium.Marker([user_lat, user_lon], tooltip="You are here",
                  icon=folium.Icon(color="blue")).add_to(m)
    folium.Marker([room_lat, room_lon], tooltip=room_choice,
                  icon=folium.Icon(color="red")).add_to(m)

    # Distance function
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371000  # meters
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c

    dist_m = haversine(user_lat, user_lon, room_lat, room_lon)

    # Try routing
    if dist_m < 50:
        # Very close → straight line
        folium.PolyLine([[user_lat, user_lon], [room_lat, room_lon]],
                        color="green", weight=4).add_to(m)
        st.info(f"🚶 Distance: {round(dist_m,1)} m | ⏱ Time: < 1 min")
    else:
        try:
            # Use OpenRouteService
            ors_url = "https://api.openrouteservice.org/v2/directions/foot-walking"
            headers = {"Authorization": "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjJkMzg4NDMwZmFkODQ3NjM5NTg3NjU2NjI2YTQxYTZhIiwiaCI6Im11cm11cjY0In0="}  # replace with your key
            body = {"coordinates": [[user_lon, user_lat], [room_lon, room_lat]]}
            response = requests.post(ors_url, json=body, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "features" in data and data["features"]:
                route = data["features"][0]["geometry"]
                folium.GeoJson(route, style_function=lambda x: {"color": "green", "weight": 4}).add_to(m)

                distance = round(data["features"][0]["properties"]["segments"][0]["distance"] / 1000, 2)
                duration = round(data["features"][0]["properties"]["segments"][0]["duration"] / 60, 1)
                st.success(f"🚶 Distance: **{distance} km** | ⏱ Time: **{duration} mins**")
            else:
                st.warning("⚠️ ORS could not find a walking route. Showing direct line.")
                folium.PolyLine([[user_lat, user_lon], [room_lat, room_lon]],
                                color="orange", weight=4, dash_array="5").add_to(m)
        except Exception:
            # Fallback to OSRM
            try:
                url = f"http://router.project-osrm.org/route/v1/foot/{user_lon},{user_lat};{room_lon},{room_lat}?overview=full&geometries=geojson"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                data = response.json()
                if data and "routes" in data and len(data["routes"]) > 0:
                    route = data["routes"][0]["geometry"]
                    folium.GeoJson(route, style_function=lambda x: {"color": "blue", "weight": 4}).add_to(m)
                    distance = round(data["routes"][0]["distance"]/1000, 2)
                    duration = round(data["routes"][0]["duration"]/60, 1)
                    st.success(f"🚶 Distance: **{distance} km** | ⏱ Time: **{duration} mins**")
                else:
                    st.warning("⚠️ No walking route found.")
            except:
                st.warning("⚠️ Could not fetch any route.")

    # Show map
    st_folium(m, width=750, height=520)

    # Footer
    st.markdown(
        """
        <div style="text-align:center; font-size:13px; color:gray; margin-top:5px;">
            🛠 Made by <b>MUT TECH CLUB</b> | 🗺 Map data from 
            <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>, 
            <a href="https://openrouteservice.org/" target="_blank">OpenRouteService</a>, 
            <a href="https://project-osrm.org/" target="_blank">OSRM</a>
        </div>
        """,
        unsafe_allow_html=True
    )

else:
    st.warning("⚠️ No rooms found. Try another search.")
