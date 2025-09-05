import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
import requests
from rapidfuzz import process  # ✅ fuzzy search

st.set_page_config(layout="wide")

# --- Session State Initialization ---
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "selected_room" not in st.session_state:
    st.session_state.selected_room = None

# Load rooms
@st.cache_data
def load_rooms():
    return pd.read_excel("campus-room-finder/rooms.xlsx")

rooms = load_rooms()

st.title("MUT Campus Room Finder")

# Map style selector
map_style = st.selectbox(
    "🗺️ Choose Map Style:",
    ["Standard", "Terrain", "Light", "Dark", "Satellite"]
)

# --- Search with Autocomplete ---
search_box = st.text_input("🔍 Search for a room:", st.session_state.search_query)

# Suggest top 5 matches using fuzzy search
suggestions = []
if search_box:
    room_names = rooms["room_name"].tolist()
    matches = process.extract(search_box, room_names, limit=5, score_cutoff=50)
    suggestions = [m[0] for m in matches]

# Display clickable suggestions under the search bar
if suggestions:
    st.markdown("**Did you mean:**")
    cols = st.columns(len(suggestions))
    for i, s in enumerate(suggestions):
        if cols[i].button(s):
            st.session_state.search_query = s
            st.session_state.selected_room = s
            st.rerun()

# Search button
if st.button("🔍 Search"):
    st.session_state.search_query = search_box
    st.rerun()

# Autocomplete dropdown (optional)
selected_from_dropdown = st.selectbox(
    "Or pick from suggestions:",
    options=[""] + suggestions,
    index=0
)

if selected_from_dropdown and selected_from_dropdown != st.session_state.selected_room:
    st.session_state.selected_room = selected_from_dropdown
    st.session_state.search_query = selected_from_dropdown
    st.rerun()

# --- Filtered Search Results ---
filtered_rooms = rooms
if st.session_state.search_query:
    substring_matches = rooms[
        rooms["room_name"].str.contains(st.session_state.search_query, case=False, na=False)
    ]
    room_names = rooms["room_name"].tolist()
    fuzzy_matches = process.extract(
        st.session_state.search_query, room_names, limit=5, score_cutoff=60
    )
    fuzzy_names = [m[0] for m in fuzzy_matches]
    fuzzy_df = rooms[rooms["room_name"].isin(fuzzy_names)]
    filtered_rooms = pd.concat([substring_matches, fuzzy_df]).drop_duplicates()

# --- Display Map and Info ---
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

    # Tile layers & attributions
    tile_layers = {
        "Standard": "OpenStreetMap",
        "Terrain": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
        "Light": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png",
        "Dark": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}{r}.png",
        "Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    }

    attributions = {
        "Standard": "© OpenStreetMap contributors",
        "Terrain": "Map tiles by Stamen Design, © OpenStreetMap",
        "Light": "© OpenStreetMap contributors © CARTO",
        "Dark": "© OpenStreetMap contributors © CARTO",
        "Satellite": "Tiles © Esri — Source: Esri, DigitalGlobe and others"
    }

    # Build map
    m = folium.Map(
        location=[user_lat, user_lon],
        zoom_start=17,
        tiles=tile_layers[map_style],
        attr=attributions[map_style]
    )

    # Markers
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

    # Show map
    st_folium(m, width=750, height=520)

    # Attribution footer
    st.markdown(
        f"""
        <div style="text-align:center; font-size:12px; color:gray; margin-top:5px;">
            🗺️ Map style: <b>{map_style}</b> <br>
            {attributions[map_style]} <br><br>
            <span style="font-size:16px; font-weight:bold; color:#228B22;">
                🚀 Made by <span style="color:#FFD700;">MUT TECH CLUB</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

else:
    st.warning("⚠️ No rooms found. Try another search.")
