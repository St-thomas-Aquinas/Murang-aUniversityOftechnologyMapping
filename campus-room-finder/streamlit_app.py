import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
import requests

st.set_page_config(layout="wide")

# Floating University Title
st.markdown(
    """
    <style>
    .app-title {
        position: fixed;
        top: 5px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 28px;
        font-weight: bold;
        color: #2E86C1;
        background: rgba(255,255,255,0.95);
        padding: 8px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        z-index: 9999;
    }
    </style>
    <div class="app-title">Murang'a University of Technology</div>
    """,
    unsafe_allow_html=True
)

# Load rooms
@st.cache_data
def load_rooms():
    return pd.read_excel("rooms.xlsx")

rooms = load_rooms()

# Main section title
st.title("🏫 Campus Room Finder")

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

    # Build map
    m = folium.Map(location=[user_lat, user_lon], zoom_start=17)
    folium.Marker([user_lat, user_lon], tooltip="You are here", icon=folium.Icon(color="blue")).add_to(m)
    folium.Marker([room_lat, room_lon], tooltip=room_choice, icon=folium.Icon(color="red")).add_to(m)

    # Route
    try:
        url = f"http://router.project-osrm.org/route/v1/foot/{user_lon},{user_lat};{room_lon},{room_lat}?overview=full&geometries=geojson"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data and "routes" in data and len(data["routes"]) > 0:
            route = data["routes"][0]["geometry"]
            folium.GeoJson(route, style_function=lambda x: {"color":"green","weight":4}).add_to(m)
            distance = round(data["routes"][0]["distance"]/1000,2)
            duration = round(data["routes"][0]["duration"]/60,1)
            st.success(f"🚶 Distance: **{distance} km** | ⏱ Time: **{duration} mins**")
    except requests.exceptions.RequestException:
        st.warning("⚠️ Could not fetch route.")

    st_folium(m, width=750, height=520)

else:
    st.warning("⚠️ No rooms found. Try another search.")
