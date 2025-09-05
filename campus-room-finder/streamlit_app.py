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
    df = df.sort_values(by="room_name", ascending=True).reset_index(drop=True)  # ✅ sort alphabetically
    return df

rooms = load_rooms()

st.title("MUT Campus Room Finder")

# Map style selector
map_style = st.selectbox(
    "🗺️ Choose Map Style:",
    ["Standard", "Terrain", "Light", "Dark", "Satellite"]
)

# --- Autocomplete + Search ---
search_query = st.text_input("🔍 Search for a room by name:")
room_names = rooms["room_name"].tolist()
room_choice = None
filtered_rooms = rooms

if search_query:
    # 1️⃣ Substring matches
    substring_matches = rooms[
        rooms["room_name"].str.contains(search_query, case=False, na=False)
    ]

    # 2️⃣ Fuzzy matches
    fuzzy_matches = process.extract(search_query, room_names, limit=5, score_cutoff=60)
    fuzzy_names = [m[0] for m in fuzzy_matches]
    fuzzy_df = rooms[rooms["room_name"].isin(fuzzy_names)]

    # Combine + sort results
    filtered_rooms = (
        pd.concat([substring_matches, fuzzy_df])
        .drop_duplicates()
        .sort_values(by="room_name", ascending=True)  # ✅ ensure sorted
    )

    # 🔥 Autocomplete suggestions
    st.write("Suggestions:")
    for name in sorted(fuzzy_names):  # ✅ sorted suggestions
        if st.button(f"➡ {name}"):
            room_choice = name

# --- Fallback dropdown ---
if not room_choice and not filtered_rooms.empty:
    room_choice = st.selectbox(
        "Select a room:",
        sorted(filtered_rooms["room_name"].unique())  # ✅ sorted dropdown
    )
