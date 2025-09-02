import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
import requests

# Load rooms data
@st.cache_data
def load_rooms():
    return pd.read_excel("rooms.xlsx")

rooms = load_rooms()

# App title
st.title(" Campus leture Room Finder")

# Search and dropdown at top (not sidebar)
search_query = st.text_input("🔍 Search by room name:")
filtered_rooms = rooms
if search_query:
    filtered_rooms = filtered_rooms[filtered_rooms["room_name"].str.contains(search_query, case=False, na=False)]

# Room dropdown
if not filtered_rooms.empty:
    room_choice = st.selectbox("Select a room:", filtered_rooms["room_name"].unique())
    room_row = filtered_rooms[filtered_rooms["room_name"] == room_choice].iloc[0]

    room_lat, room_lon = room_row["lat"], room_row["lon"]

    # Room info card
    st.markdown(
        f"""
        <div style="padding:15px; background:#f9f9f9; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.1); margin-bottom:15px;">
            <h3 style="margin:0;">📍 {room_row['room_name']}</h3>
            <p style="margin:0;">🏢 Building: <b>{room_row['building']}</b></p>
            <p style="margin:0;">🛗 Floor: <b>{room_row['floor']}</b></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Get user location
    user_loc = get_geolocation()
    if user_loc is not None:
        user_lat, user_lon = user_loc["coords"]["latitude"], user_loc["coords"]["longitude"]

        # Request walking route from OSRM API
        url = f"http://router.project-osrm.org/route/v1/foot/{user_lon},{user_lat};{room_lon},{room_lat}?overview=full&geometries=geojson"
        response = requests.get(url)

        # Map
        m = folium.Map(location=[user_lat, user_lon], zoom_start=17)

        # Markers
        folium.Marker([user_lat, user_lon], tooltip="📍 You are here", icon=folium.Icon(color="blue")).add_to(m)
        folium.Marker([room_lat, room_lon], tooltip=room_choice, icon=folium.Icon(color="red")).add_to(m)

        # Route drawing
        if response.status_code == 200:
            data = response.json()
            if data and "routes" in data and len(data["routes"]) > 0:
                route = data["routes"][0]["geometry"]
                distance = round(data["routes"][0]["distance"] / 1000, 2)
                duration = round(data["routes"][0]["duration"] / 60, 1)

                folium.GeoJson(
                    route, 
                    name="route", 
                    style_function=lambda x: {"color": "green", "weight": 4}
                ).add_to(m)

                # Show distance and time
                st.success(f"🚶 Distance: **{distance} km** | ⏱ Time: **{duration} mins**")

        # Adjust map to fit both points
        m.fit_bounds([[user_lat, user_lon], [room_lat, room_lon]])

        # Show map
        st_folium(m, width=750, height=520)

    else:
        st.info("📍 Please allow location access in your browser to see the route.")
else:
    st.warning("⚠️ No rooms found. Try another search.")

