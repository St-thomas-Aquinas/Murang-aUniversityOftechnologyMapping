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

st.title("Campus Room Finder 🏫")

# Show available columns (for debugging if needed)
# st.write("Excel columns:", rooms.columns.tolist())

# Let user select a room by name
room_choice = st.selectbox("Select a room:", rooms["room_name"].unique())
room_row = rooms[rooms["room_name"] == room_choice].iloc[0]

room_lat, room_lon = room_row["lat"], room_row["lon"]

# Get user location from browser
user_loc = get_geolocation()
if user_loc is not None:
    user_lat, user_lon = user_loc["coords"]["latitude"], user_loc["coords"]["longitude"]

    # Call OSRM API for route
    url = f"http://router.project-osrm.org/route/v1/driving/{user_lon},{user_lat};{room_lon},{room_lat}?overview=full&geometries=geojson"
    response = requests.get(url)

    m = folium.Map(location=[user_lat, user_lon], zoom_start=17)

    # Add markers
    folium.Marker([user_lat, user_lon], tooltip="You are here", icon=folium.Icon(color="blue")).add_to(m)
    folium.Marker([room_lat, room_lon], tooltip=room_choice, icon=folium.Icon(color="red")).add_to(m)

    # Draw route if found
    if response.status_code == 200:
        data = response.json()
        if data and "routes" in data and len(data["routes"]) > 0:
            route = data["routes"][0]["geometry"]
            folium.GeoJson(route, name="route").add_to(m)
        else:
            st.warning("⚠️ No route found between your location and this room.")
    else:
        st.error("❌ Error fetching route from OSRM API.")

    st_folium(m, width=700, height=500)

else:
    st.info("📍 Please allow location access in your browser to see the route.")
