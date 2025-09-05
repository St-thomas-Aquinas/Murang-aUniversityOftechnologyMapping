import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
import requests
import difflib

# Try to import rapidfuzz for better fuzzy matching; fall back to difflib if missing
try:
    from rapidfuzz import process as rf_process
    _USE_RAPIDFUZZ = True
except Exception:
    rf_process = None
    _USE_RAPIDFUZZ = False

st.set_page_config(layout="wide")

# ---------- Load & prepare data ----------
@st.cache_data
def load_rooms():
    df = pd.read_excel("campus-room-finder/rooms.xlsx")  # adjust path if needed
    # normalize and sort alphabetically on load
    df = df.sort_values(by="room_name", key=lambda s: s.str.lower()).reset_index(drop=True)
    return df

rooms = load_rooms()

st.title("MUT Campus Room Finder")

# ---------- UI: map style ----------
map_style = st.selectbox(
    "🗺️ Choose Map Style:",
    ["Standard", "Terrain", "Light", "Dark", "Satellite"]
)

# ---------- Session state defaults ----------
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "selected_room" not in st.session_state:
    st.session_state.selected_room = ""  # holds the chosen room name (from suggestion or dropdown)

# ---------- Search input (autocomplete-enabled) ----------
search_col, _ = st.columns([3, 1])
with search_col:
    # text_input bound to session_state so it persists across reruns
    st.text_input("🔍 Search for a room by name:", key="search_query", placeholder="Type room name, building or partial...")

# Prepare list of all room names (already sorted)
all_room_names = rooms["room_name"].astype(str).tolist()

# Compute suggestions when typing
suggestions = []
query = st.session_state.search_query.strip()
if query:
    # 1) Substring matches (case-insensitive, preserve room order)
    substring_mask = rooms["room_name"].str.contains(query, case=False, na=False)
    substring_names = rooms.loc[substring_mask, "room_name"].tolist()

    # 2) Fuzzy matches (rapidfuzz preferred, otherwise difflib)
    fuzzy_names = []
    if _USE_RAPIDFUZZ:
        # rapidfuzz gives (name, score, idx) tuples
        fuzzy = rf_process.extract(query, all_room_names, limit=8, score_cutoff=60)
        fuzzy_names = [t[0] for t in fuzzy]
    else:
        # difflib fallback (cutoff roughly similar; returns list)
        fuzzy_names = difflib.get_close_matches(query, all_room_names, n=8, cutoff=0.6)

    # Combine suggestions: substring first, then fuzzy (dedup)
    seen = set()
    for n in substring_names + fuzzy_names:
        if n not in seen:
            suggestions.append(n)
            seen.add(n)
    # limit suggestions to a reasonable number
    suggestions = suggestions[:6]

# ---------- Show suggestions as clickable buttons ----------
if suggestions:
    st.markdown("**Suggestions:**")
    # show each suggestion with a small "select" button
    for name in suggestions:
        cols = st.columns([0.9, 0.1])
        cols[0].markdown(f"**{name}**")
        # unique key for each button to avoid collisions
        btn_key = f"select__{name}"
        if cols[1].button("Select", key=btn_key):
            # set selection in session state; also update search box to the selected name
            st.session_state.selected_room = name
            st.session_state.search_query = name
            # immediate feedback
            st.experimental_rerun()  # rerun so the dropdown shows the selected value

# ---------- Build filtered_rooms (based on query) ----------
if query:
    substring_matches = rooms[rooms["room_name"].str.contains(query, case=False, na=False)]
    fuzzy_df = rooms[rooms["room_name"].isin([n for n in suggestions])]
    filtered_rooms = pd.concat([substring_matches, fuzzy_df]).drop_duplicates().reset_index(drop=True)
else:
    filtered_rooms = rooms.copy()

# Ensure filtered_rooms is sorted A→Z by room_name (case-insensitive)
filtered_rooms = filtered_rooms.sort_values(by="room_name", key=lambda s: s.str.lower()).reset_index(drop=True)

# ---------- Dropdown fallback (sorted) ----------
if not filtered_rooms.empty:
    choices = filtered_rooms["room_name"].astype(str).tolist()

    # Determine selected index for the selectbox
    default_index = 0
    if st.session_state.selected_room and st.session_state.selected_room in choices:
        default_index = choices.index(st.session_state.selected_room)

    # Show dropdown and update session_state on selection
    selected_from_dropdown = st.selectbox("Or pick from the list:", choices, index=default_index)
    if selected_from_dropdown != st.session_state.selected_room:
        st.session_state.selected_room = selected_from_dropdown
        st.session_state.search_query = selected_from_dropdown

    # final room choice
    room_choice = st.session_state.selected_room

    # get the row for that room (safe lookup)
    room_row = rooms[rooms["room_name"] == room_choice].iloc[0]
    room_lat, room_lon = float(room_row["lat"]), float(room_row["lon"])

    # show room card
    st.markdown(
        f"""
        <div style="padding:15px; background:#f9f9f9; border-radius:10px;">
            <h3>📍 {room_row['room_name']}</h3>
            <p>🏢 Building: <b>{room_row['building']}</b></p>
            <p>🛗 Floor: <b>{room_row['floor']}</b></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------- Get GPS ----------
    default_lat, default_lon = -0.748, 37.150
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
        default=None,
    )
    if user_coords:
        user_lat, user_lon = float(user_coords["lat"]), float(user_coords["lon"])
    else:
        user_lat, user_lon = default_lat, default_lon
        st.info("📍 GPS not available. Showing campus center.")

    # ---------- Tile layers and attributions ----------
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

    # ---------- Build map (with required attribution) ----------
    m = folium.Map(
        location=[user_lat, user_lon],
        zoom_start=17,
        tiles=tile_layers[map_style],
        attr=attributions[map_style],
    )

    # markers
    folium.Marker([user_lat, user_lon], tooltip="You are here", icon=folium.Icon(color="blue")).add_to(m)
    folium.Marker([room_lat, room_lon], tooltip=room_choice, icon=folium.Icon(color="red")).add_to(m)

    # ---------- Routing (OSRM as before) ----------
    try:
        url = f"http://router.project-osrm.org/route/v1/foot/{user_lon},{user_lat};{room_lon},{room_lat}?overview=full&geometries=geojson"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data and "routes" in data and len(data["routes"]) > 0:
            route = data["routes"][0]["geometry"]
            folium.GeoJson(route, style_function=lambda x: {"color": "green", "weight": 4}).add_to(m)
            distance = round(data["routes"][0]["distance"] / 1000, 2)
            duration = round(data["routes"][0]["duration"] / 60, 1)
            st.success(f"🚶 Distance: **{distance} km** | ⏱ Time: **{duration} mins**")
    except requests.exceptions.RequestException:
        st.warning("⚠️ Could not fetch route. Showing markers only.")

    # show map
    st_folium(m, width=750, height=520)

    # footer attribution & credit
    st.markdown(
        f"""
        <div style="text-align:center; font-size:12px; color:gray; margin-top:8px;">
            🗺️ Map style: <b>{map_style}</b> <br>
            {attributions[map_style]} <br><br>
            <span style="font-size:16px; font-weight:bold; color:#228B22;">
                🚀 Made by <span style="color:#FFD700;">MUT TECH CLUB</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

else:
    st.warning("⚠️ No rooms found. Try another search.")
