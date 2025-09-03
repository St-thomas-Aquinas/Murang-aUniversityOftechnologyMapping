import streamlit as st 
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
import requests
import time

# ----------------- UI CLEANUP -----------------
hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;} 
    footer {visibility: hidden;}    
    header {visibility: hidden;}    
    .viewerBadge_link__qRIco {display: none !important;}  /* Streamlit logo */
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ----------------- LOAD DATA -----------------
@st.cache_data
def load_rooms():
    return pd.read_excel("rooms.xlsx")

rooms = load_rooms()

# ----------------- CUSTOM LAYOUT -----------------
st.markdown(
    """
    <style>
    .block-container {
        padding: 0;   /* remove Streamlit padding */
    }
    .fullscreen-map {
        position: fixed;
        top: 0;
        left: 0;
        height: 100vh;
        width: 100vw;
        z-index: 1;
    }
    .search-box {
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: white;
        padding: 10px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 9999;
        width: 320px;
    }
    .info-card {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: white;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 9999;
        width: 340px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------- SEARCH BAR -----------------
st.markdown('<div class="search-box">', unsafe_allow_html=True)
search_query = st.text_input("🔍 Search for a room", key="floating_search")
st.markdown('</div>', unsafe_allow_html=True)

# ----------------- FILTER ROOMS -----------------
filtered_rooms = rooms
if search_query:
    filtered_rooms = filtered_rooms[
        filtered_rooms["room_name"].str.contains(search_query, case=False, na=False)
    ]

if not filtered_rooms.empty:
    room_choice = st.selectbox(
        "Select a room:", 
        filtered_rooms["room_name"].unique(), 
        key="room_select"
    )
    room_row = filtered_rooms[filtered_rooms["room_name"] == room_choice].iloc[0]

    room_lat, room_lon = room_row["lat"], room_row["lon"]

    # ----------------- GPS HANDLING -----------------
    default_lat, default_lon = -0.748, 37.150  # fallback campus center
    user_coords = streamlit_js_eval(
        js_expressions="""
        new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
                pos => resolve({lat: pos.coords.latitude, lon: pos.coords.longitude}),
                err => resolve(null)
            );
        })
        """,
        key="gps_async",
        default=None
    )

    attempts = 0
    while user_coords is None and attempts < 3:
        time.sleep(1)
        user_coords = streamlit_js_eval(
            js_expressions="""
            new Promise((resolve, reject) => {
                navigator.geolocation.getCurrentPosition(
                    pos => resolve({lat: pos.coords.latitude, lon: pos.coords.longitude}),
                    err => resolve(null)
                );
            })
            """,
            key=f"gps_async_{attempts}",
            default=None
        )
        attempts += 1

    if user_coords:
        user_lat, user_lon = user_coords["lat"], user_coords["lon"]
    else:
        user_lat, user_lon = default_lat, default_lon

    # ----------------- OSRM DIRECTIONS -----------------
    url = f"http://router.project-osrm.org/route/v1/foot/{user_lon},{user_lat};{room_lon},{room_lat}?overview=full&geometries=geojson"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        response = None

    # ----------------- BUILD MAP -----------------
    m = folium.Map(location=[user_lat, user_lon], zoom_start=17)

    folium.Marker([user_lat, user_lon], tooltip="You are here", icon=folium.Icon(color="blue")).add_to(m)
    folium.Marker([room_lat, room_lon], tooltip=room_choice, icon=folium.Icon(color="red")).add_to(m)

    if response:
        data = response.json()
        if data and "routes" in data and len(data["routes"]) > 0:
            route = data["routes"][0]["geometry"]
            distance = round(data["routes"][0]["distance"] / 1000, 2)
            duration = round(data["routes"][0]["duration"] / 60, 1)
            folium.GeoJson(route, style_function=lambda x: {"color": "green", "weight": 4}).add_to(m)
            info_html = f"🚶 {distance} km | ⏱ {duration} mins"
        else:
            info_html = "⚠️ No route found"
    else:
        info_html = "⚠️ Could not fetch route"

    m.fit_bounds([[user_lat, user_lon], [room_lat, room_lon]])

    # ----------------- SHOW MAP -----------------
    st_folium(m, width=None, height=700)

    # ----------------- FLOATING INFO CARD -----------------
    st.markdown(
        f"""
        <div class="info-card">
            <h4 style="margin:0;">📍 {room_row['room_name']}</h4>
            <p style="margin:0;">🏢 {room_row['building']}</p>
            <p style="margin:0;">🛗 Floor: {room_row['floor']}</p>
            <p style="margin:0;">{info_html}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

else:
    st.warning("⚠️ No rooms found. Try another search.")
