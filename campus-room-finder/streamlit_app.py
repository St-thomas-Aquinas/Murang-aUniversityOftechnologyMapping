import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from rapidfuzz import process  # fuzzy search

# -------------------------
# Mock dataset (replace with your real campus data)
# -------------------------
data = {
    "room_name": ["Library", "Lab 1", "Lab 2", "Administration", "Hall A", "Hall B"],
    "lat": [-0.785, -0.786, -0.787, -0.784, -0.783, -0.782],
    "lon": [36.955, 36.956, 36.957, 36.958, 36.959, 36.960],
}
rooms_df = pd.DataFrame(data)

# -------------------------
# Initialize session state
# -------------------------
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "selected_room" not in st.session_state:
    st.session_state.selected_room = None

st.title("🏫 Campus Room Finder (MUT)")

# -------------------------
# Search Input + Button
# -------------------------
col1, col2 = st.columns([4, 1])
with col1:
    search_box = st.text_input(
        "Search for a room:",
        value=st.session_state.search_query,
        key="room_input"
    )
with col2:
    if st.button("🔍 Search"):
        st.session_state.search_query = search_box
        st.experimental_rerun()

# -------------------------
# Autocomplete (fuzzy search)
# -------------------------
if search_box.strip():
    matches = process.extract(
        search_box,
        rooms_df["room_name"].astype(str),
        limit=5,
        score_cutoff=40
    )
    suggestions = [m[0] for m in matches]
else:
    suggestions = []

if suggestions:
    st.write("Suggestions:")
    for s in suggestions:
        if st.button(s):
            st.session_state.search_query = s
            st.session_state.selected_room = s
            st.experimental_rerun()

# -------------------------
# Dropdown (sorted list)
# -------------------------
choices = sorted(rooms_df["room_name"].tolist())
default_index = 0
if st.session_state.selected_room and st.session_state.selected_room in choices:
    default_index = choices.index(st.session_state.selected_room)

selected_from_dropdown = st.selectbox(
    "Or pick from the list:",
    choices,
    index=default_index,
    key="room_dropdown"
)

if selected_from_dropdown != st.session_state.selected_room:
    st.session_state.selected_room = selected_from_dropdown
    if "search_query" in st.session_state:
        del st.session_state["search_query"]
    st.session_state.search_query = selected_from_dropdown
    st.experimental_rerun()

# -------------------------
# Display Map
# -------------------------
if st.session_state.selected_room:
    room_data = rooms_df[rooms_df["room_name"] == st.session_state.selected_room].iloc[0]
    st.success(f"Showing location for: {st.session_state.selected_room}")

    m = folium.Map(
        location=[room_data["lat"], room_data["lon"]],
        zoom_start=18,
        tiles="OpenStreetMap",
        attr="Map data © OpenStreetMap contributors"
    )
    folium.Marker(
        [room_data["lat"], room_data["lon"]],
        popup=room_data["room_name"],
        tooltip="You are here"
    ).add_to(m)

    st_folium(m, width=700, height=500)

# -------------------------
# Footer
# -------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center; font-weight:bold; color:#E74C3C;'>✨ Made by MUT TECH CLUB ✨</p>",
    unsafe_allow_html=True
)
