import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
import requests
import time

# Hide Streamlit default header, footer, and menu
st.markdown("""
<style>
#MainMenu {visibility: hidden;} 
footer {visibility: hidden;}    
header {visibility: hidden;}    
</style>
""", unsafe_allow_html=True)

# Load rooms data
@st.cache_data
def load_rooms():
    return pd.read_excel("rooms.xlsx")

rooms = load_rooms()
st.title("🏫 Campus Room Finder")

# Search input
search_query = st.text_input("🔍 Search for a room by name:")

# Filter rooms
filtered_rooms = rooms
if search_query:
    filtered_rooms = filtered_rooms[
        filtered_rooms["room_name"].str.contains(search_query, case=False, na=False)
    ]

if not filtered_rooms.empty:
    room_choice = st.selectbox("Select a room:", filtered_rooms["room_name"].unique())
    room_row = filtered_rooms[filtered_rooms["room_name"] == room_choice].iloc[0]
    room_lat, room_lon = room_row["lat"], room_row["lon"]

    # Room info card
    st.markdown(f"""
    <div style="padding:15px; background:#f9f9f9; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1);">
        <h3 style="margin:0;">📍 {room_row['room_name']}</h3>
        <p style="margin:0;">🏢 Building: <b>{room_row['building']}</b></p>
        <p style="margin:0;">🛗 Floor: <b>{room_row['floor']}</b></p>
    </div>
    """, unsafe_allow_html=True)

    # Default campus center
    default_lat, default_lon = -0.748, 37.150

    st.info("📍 Waiting for GPS updates... Blue marker and route will update in real time.")

    # Initialize map
    m = folium.Map(location=[default_lat, default_lon], zoom_start=17)
    room_marker = folium.Marker([room_lat, room_lon], tooltip=room_choice, icon=folium.Icon(color="red"))
    room_marker.add_to(m)
    map_container = st_folium(m, width=750, height=520)

    user_marker = None
    route_layer = None

    # Live GPS loop (updates every 2 seconds)
    for i in range(60):  # run for ~2 minutes
        user_coords = streamlit_js_eval(
            js_expressions="""
            new Promise((resolve) => {
                navigator.geolocation.getCurrentPosition(
                    pos => resolve({lat: pos.coords.latitude, lon: pos.coords.longitude}),
                    err => resolve(null)
                );
            })
            """,
            key=f"gps_live_{i}",
            default=None
        )

        if user_coords:
            user_lat, user_lon = user_coords["lat"], user_coords["lon"]
            st.success(f"✅ GPS detected: {user_lat}, {user_lon}")

            # Remove previous user marker
            if user_marker:
                m.remove_child(user_marker)

            # Add new user marker
            user_marker = folium.Marker([user_lat, user_lon], tooltip="You are here", icon=folium.Icon(color="blue"))
            user_marker.add_to(m)

            # Remove previous route layer
            if route_layer:
                m.remove_child(route_layer)

            # Draw walking route
            try:
                url = f"http://router.project-osrm.org/route/v1/foot/{user_lon},{user_lat};{room_lon},{room_lat}?overview=full&geometries=geojson"
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                data = response.json()
                if data and "routes" in data and len(data["routes"]) > 0:
                    route = data["routes"][0]["geometry"]
                    distance = round(data["routes"][0]["distance"]/1000, 2)
                    duration = round(data["routes"][0]["duration"]/60, 1)
                    route_layer = folium.GeoJson(route, style_function=lambda x: {"color":"green","weight":4})
                    route_layer.add_to(m)
                    st.success(f"🚶 Distance: **{distance} km** | ⏱ Time: **{duration} mins**")
            except requests.exceptions.RequestException:
                st.warning("⚠️ Could not fetch route this update.")

            # Update map
            map_container = st_folium(m, width=750, height=520)
        else:
            st.warning("📍 GPS not yet available...")

        time.sleep(2)

else:
    st.warning("⚠️ No rooms found. Try another search.")
