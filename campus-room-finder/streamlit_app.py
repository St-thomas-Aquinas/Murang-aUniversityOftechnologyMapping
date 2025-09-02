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

# 🔍 Search bar for room name
search_query = st.text_input("Search for a room by name:")

filtered_rooms = rooms[rooms["room_name"].str.contains(search_query, case=False, na=False)] if search_query else rooms

if not filtered_rooms.empty:
    room_choice = st.selectbox("Select a room:", filtered_rooms["room_name"].unique())
    room_row = filtered_rooms[filtered_rooms["room_name"] == room_choice].iloc[0]

    room_lat, room_lon = room_row["lat"], room_row["lon"]

    # Show room details
    st.write(f"**Building:** {room_row['building']}, **Floor:** {room_row['floor']}")

    # Get user location
    user_loc = get_geolocation()
    if user_loc is not None:
        user_lat, user_lon = user_loc["coords"]["latitude"], user_loc["coords"]["longitude"]

        # Call OSRM API for route
        url = f"http://router.project-osrm.org/route/v1/driving/{user_lon},{user_lat};{room_lon},{room_lat}?overview=full&geometries=geojson"
        response = requests.get(url)

        # Initialize map (center temporary on user)
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
            st.error("❌ Error fetching route from OSRM API.")

        # ✅ Auto-zoom to fit both points
        m.fit_bounds([[user_lat, user_lon], [room_lat, room_lon]])

        # Show map
        st_folium(m, width=700, height=500)

    else:
        st.info("📍 Please allow location access in your browser to see the route.")
else:
    st.warning("No rooms found matching your search.")
