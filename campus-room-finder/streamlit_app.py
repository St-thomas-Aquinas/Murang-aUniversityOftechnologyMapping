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

st.set_page_config(page_title="Campus Room Finder", layout="wide")

st.title("🏫 Campus Room Finder")

# Search & filters inside expander (better for mobile)
with st.expander("🔍 Search & Filters", expanded=True):
    search_query = st.text_input("Search room name:")
    building_filter = st.selectbox("Building:", ["All"] + sorted(rooms["building"].unique().tolist()))
    floor_filter = st.selectbox("Floor:", ["All"] + sorted(rooms["floor"].astype(str).unique().tolist()))

# Apply filters
filtered_rooms = rooms
if search_query:
    filtered_rooms = filtered_rooms[filtered_rooms["room_name"].str.contains(search_query, case=False, na=False)]
if building_filter != "All":
    filtered_rooms = filtered_rooms[filtered_rooms["building"] == building_filter]
if floor_filter != "All":
    filtered_rooms = filtered_rooms[filtered_rooms["floor"].astype(str) == floor_filter]

# Room selection list (mobile friendly)
room_choice = None
if not filtered_rooms.empty:
    st.subheader("Available Rooms")
    for _, row in filtered_rooms.iterrows():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(
                f"""
                <div style="padding:10px; background:#f9f9f9; border-radius:8px; margin-bottom:8px;
                            font-size:18px;">
                    📍 <b>{row['room_name']}</b><br>
                    🏢 {row['building']} | 🛗 Floor {row['floor']}
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col2:
            if st.button("Select", key=row["room_id"]):
                room_choice = row["room_name"]

# Continue only if room selected
if room_choice:
    room_row = rooms[rooms["room_name"] == room_choice].iloc[0]
    room_lat, room_lon = room_row["lat"], room_row["lon"]

    st.success(f"Showing route to **{room_row['room_name']}**")

    # Get user location
    user_loc = get_geolocation()
    if user_loc is not None:
        user_lat, user_lon = user_loc["coords"]["latitude"], user_loc["coords"]["longitude"]

        # OSRM route
        url = f"http://router.project-osrm.org/route/v1/foot/{user_lon},{user_lat};{room_lon},{room_lat}?overview=full&geometries=geojson"
        response = requests.get(url)

        # Map setup
        m = folium.Map(location=[user_lat, user_lon], zoom_start=17)

        folium.Marker([user_lat, user_lon], tooltip="📍 You are here", icon=folium.Icon(color="blue")).add_to(m)
        folium.Marker([room_lat, room_lon], tooltip=room_choice, icon=folium.Icon(color="red")).add_to(m)

        if response.status_code == 200:
            data = response.json()
            if data and "routes" in data and len(data["routes"]) > 0:
                route = data["routes"][0]["geometry"]
                distance = round(data["routes"][0]["distance"] / 1000, 2)
                duration = round(data["routes"][0]["duration"] / 60, 1)

                folium.GeoJson(route, style_function=lambda x: {"color": "green", "weight": 5}).add_to(m)
                st.info(f"🚶 Distance: **{distance} km** | ⏱ {duration} mins walk")

        m.fit_bounds([[user_lat, user_lon], [room_lat, room_lon]])
        st_folium(m, width=400, height=500)  # optimized for mobile
    else:
        st.warning("📍 Enable location access to see your route.")
else:
    st.info("ℹ️ Search and select a room above.")
