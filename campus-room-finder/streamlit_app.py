import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
import requests

# ============================
# Load Excel (rooms database)
# ============================
@st.cache_data
def load_rooms():
    return pd.read_excel("rooms.xlsx")  # file must be in same folder

rooms = load_rooms()

st.title("📍 School Room Finder")
st.write("Search for a room and get the route from your current location.")

# ============================
# User selects room
# ============================
room_choice = st.selectbox("Select a room:", rooms["Room"])

# Get destination coordinates
dest_row = rooms[rooms["Room"] == room_choice].iloc[0]
dest_lat, dest_lon = dest_row["Latitude"], dest_row["Longitude"]

# ============================
# Get user location (browser)
# ============================
loc = get_geolocation()
if loc is not None:
    user_lat, user_lon = loc["coords"]["latitude"], loc["coords"]["longitude"]
    has_coords = True
else:
    st.warning("⚠️ Could not get your location. Please allow location access in your browser.")
    has_coords = False

# ============================
# Create map
# ============================
m = folium.Map(location=[dest_lat, dest_lon], zoom_start=17)

# Destination marker
folium.Marker(
    [dest_lat, dest_lon],
    popup=f"Room {room_choice}",
    tooltip=f"Room {room_choice}",
    icon=folium.Icon(color="red", icon="info-sign")
).add_to(m)

# ============================
# If user location available
# ============================
if has_coords:
    # User marker
    folium.Marker(
        [user_lat, user_lon],
        popup="You are here",
        tooltip="Your location",
        icon=folium.Icon(color="blue", icon="user")
    ).add_to(m)

    # --- OSRM ROUTE ---
    osrm_url = f"http://router.project-osrm.org/route/v1/walking/{user_lon},{user_lat};{dest_lon},{dest_lat}?overview=full&geometries=geojson"

    try:
        res = requests.get(osrm_url)
        data = res.json()

        if "routes" in data and len(data["routes"]) > 0:
            route = data["routes"][0]["geometry"]["coordinates"]

            if route:
                # Convert (lon,lat) → (lat,lon)
                route_latlon = [(lat, lon) for lon, lat in route]

                # Draw polyline
                folium.PolyLine(
                    locations=route_latlon,
                    color="green",
                    weight=4,
                    opacity=0.8,
                    tooltip="Walking route"
                ).add_to(m)

                # Zoom to fit both markers
                m.fit_bounds([ [user_lat, user_lon], [dest_lat, dest_lon] ])

                # Show distance + duration
                distance = data["routes"][0]["distance"] / 1000  # km
                duration = data["routes"][0]["duration"] / 60    # minutes
                st.success(f"✅ Route found: **{distance:.2f} km**, about **{duration:.1f} minutes** walking.")
            else:
                st.warning("⚠️ No route geometry returned.")
        else:
            st.warning("⚠️ No route found. Try another location.")

    except Exception as e:
        st.error(f"❌ Error fetching route: {e}")

# ============================
# Show map
# ============================
st_data = st_folium(m, width=700, height=500)
