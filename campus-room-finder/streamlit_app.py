import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
import requests
from rapidfuzz import process  # ✅ fuzzy search

st.set_page_config(layout="wide")

# Load rooms
@st.cache_data
def load_rooms():
    df = pd.read_excel("campus-room-finder/rooms.xlsx")
    # ✅ Sort all rooms alphabetically by name on load
    return df.sort_values(by="room_name", key=lambda col: col.str.lower())

rooms = load_rooms()

st.title("MUT Campus Room Finder")

# Map style selector (works on mobile too)
map_style = st.selectbox(
    "🗺️ Choose Map Style:",
    ["Standard", "Terrain", "Light", "Dark", "Satellite"]
)

# --- Search ---
search_query = st.text_input("🔍 Search for a room by name:")
filtered_rooms = rooms

if search_query:
    # 1️⃣ Case-insensitive substring match
    substring_matches = rooms[
        rooms["room_name"].str.contains(search_query, case=False, na=False)
    ]

    # 2️⃣ Fuzzy match (top 5 similar names)
    room_names = rooms["room_name"].tolist()
    fuzzy_matches = process.extract(
        search_query, room_names, limit=5, score_cutoff=60
    )
    fuzzy_names = [m[0] for m in fuzzy_matches]

    fuzzy_df = rooms[rooms["room_name"].isin(fuzzy_names)]

    # Combine both (remove duplicates) and sort alphabetically
    filtered_rooms = (
        pd.concat([substring_matches, fuzzy_df])
        .drop_duplicates()
        .sort_values(by="room_name", key=lambda col: col.str.lower())
    )

if not filtered_rooms.empty:
    # ✅ Already sorted from above
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
                pos => resolve({lat: pos.coords.latitude, lon: pos.coords.longitude})
