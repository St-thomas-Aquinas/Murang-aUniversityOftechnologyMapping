import streamlit as st
import json
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
import requests
from rapidfuzz import process  # ✅ fuzzy search
import csv
from typing import List, Tuple
from pathlib import Path
from branca.element import Element
import re

st.set_page_config(layout="wide")


# simple ray-casting point-in-polygon
def point_in_polygon(lat: float, lon: float, poly: List[Tuple[float, float]]) -> bool:
    x = lon
    y = lat
    inside = False
    n = len(poly)
    if n == 0:
        return False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i][1], poly[i][0]  # poly stored as (lat, lon)
        xj, yj = poly[j][1], poly[j][0]
        intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
        if intersect:
            inside = not inside
        j = i
    return inside


@st.cache_data
def load_rooms():
    p = Path("campus-room-finder/rooms.json")
    with p.open("r", encoding="utf-8") as f:
        rooms_list = json.load(f)
    for r in rooms_list:
        if "floor" in r and r["floor"] is not None:
            r["floor"] = str(r["floor"])
        else:
            r["floor"] = ""
        r.setdefault("room_name", "")
        r.setdefault("lat", None)
        r.setdefault("lon", None)
        r.setdefault("building", "")
    rooms_list = sorted(rooms_list, key=lambda x: x.get("room_name", "").lower())
    return rooms_list


@st.cache_data
def load_boundary() -> List[Tuple[float, float]]:
    # Expecting campus-room-finder/boundaries.csv with header lat,lon and rows in polygon order
    poly = []
    p = Path("campus-room-finder/boundaries.csv")
    print("Boundaries not found!" if not p.exists() else "Boundaries found.")
    if not p.exists():
        return []
    with p.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                wkt = (row.get("WKT") or row.get("wkt") or "").strip()
                if wkt:
                    m = re.search(r"POINT\s*\(\s*(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*\)", wkt, re.IGNORECASE)
                    if not m:
                        m = re.search(r"(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)", wkt)
                    if not m:
                        raise ValueError("no coords in WKT")
                    lat = float(m.group(1))
                    lon = float(m.group(2))
                else:
                    lat = float(row.get("lat") or row.get("latitude") or row.get("y"))
                    lon = float(row.get("lon") or row.get("longitude") or row.get("x"))
                poly.append((lat, lon))
            except (TypeError, ValueError):
                continue
            except (TypeError, ValueError):
                continue
    return poly


rooms = load_rooms()
boundary_poly = load_boundary()

st.title("MUT Campus Room Finder")

if not boundary_poly:
    st.error("Campus boundary not found (campus-room-finder/boundaries.csv). Admin must provide it.")
    st.stop()

# compute bounding box for map restrictions
lats = [pt[0] for pt in boundary_poly]
lons = [pt[1] for pt in boundary_poly]
min_lat, max_lat = min(lats), max(lats)
min_lon, max_lon = min(lons), max(lons)
bounds = [[min_lat, min_lon], [max_lat, max_lon]]

# Map style selector
map_style = st.selectbox(
    "🗺️ Choose Map Style:",
    ["Standard", "Terrain", "Light", "Dark", "Satellite"]
)

# Get GPS early and enforce boundary-based access control
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

# Deny access if GPS unavailable or user not inside polygon
# if not user_coords:
if True:
    # large 404 page
    st.markdown(
        """
        <div style="display:flex; align-items:center; justify-content:center; height:70vh; flex-direction:column;">
            <h1 style="font-size:96px; margin:0;">403</h1>
            <h2 style="font-size:28px; margin:0;">Access Denied</h2>
            <p style="color:gray; max-width:700px; text-align:center;">
                GPS is not available. This service is restricted to users physically within the MUT campus boundaries.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

user_lat, user_lon = user_coords["lat"], user_coords["lon"]
if not point_in_polygon(user_lat, user_lon, boundary_poly):
    st.markdown(
        """
        <div style="display:flex; align-items:center; justify-content:center; height:70vh; flex-direction:column;">
            <h1 style="font-size:96px; margin:0;">404</h1>
            <h2 style="font-size:28px; margin:0;">Access Denied</h2>
            <p style="color:gray; max-width:700px; text-align:center;">
                You are outside the MUT campus boundaries. This application is only accessible from within campus.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# --- Autocomplete + Search ---
search_query = st.text_input("🔍 Search for a room by name:")
room_names = [r["room_name"] for r in rooms]
room_choice = None
filtered_rooms = rooms.copy()

if search_query:
    substring_matches = [
        r for r in rooms if search_query.lower() in r.get("room_name", "").lower()
    ]
    fuzzy_matches = process.extract(search_query, room_names, limit=5, score_cutoff=60)
    fuzzy_names = [m[0] for m in fuzzy_matches]
    fuzzy_df = [r for r in rooms if r.get("room_name") in fuzzy_names]
    combined = {r["room_name"]: r for r in (substring_matches + fuzzy_df)}.values()
    filtered_rooms = sorted(combined, key=lambda x: x.get("room_name", "").lower())
    st.write("Suggestions:")
    for name in sorted(fuzzy_names):
        if st.button(f"➡ {name}"):
            room_choice = name

# Fallback dropdown
if not room_choice and len(filtered_rooms) > 0:
    room_choice = st.selectbox(
        "Select a room:",
        sorted({r["room_name"] for r in filtered_rooms})
    )

# Show room on map
if room_choice:
    room_row = next((r for r in rooms if r["room_name"] == room_choice), None)
    if room_row is None:
        st.warning("⚠️ Selected room not found.")
    else:
        room_lat, room_lon = room_row["lat"], room_row["lon"]

        st.markdown(f"""
        <div style="padding:15px; background:#f9f9f9; border-radius:10px;">
            <h3>📍 {room_row['room_name']}</h3>
            <p>🏢 Building: <b>{room_row['building']}</b></p>
            <p>🛗 Floor: <b>{room_row['floor']}</b></p>
        </div>
        """, unsafe_allow_html=True)

        # Tile layers
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

        # Build map centered on user but bounded to campus bbox
        m = folium.Map(
            location=[user_lat, user_lon],
            zoom_start=17,
            tiles=tile_layers[map_style],
            attr=attributions[map_style],
            control_scale=True,
            max_bounds=True
        )

        # draw campus polygon
        folium.Polygon(
            locations=[(lat, lon) for lat, lon in boundary_poly],
            color="blue",
            weight=3,
            fill=True,
            fill_opacity=0.05,
            tooltip="MUT Campus Boundary"
        ).add_to(m)

        # set map to fit campus bounds
        m.fit_bounds(bounds)

        # inject JS to strictly set map max bounds to campus bbox
        bounds_js = f"[[{min_lat}, {min_lon}], [{max_lat}, {max_lon}]]"
        script = Element(f"""
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(function() {{
                for (var k in window) {{
                    if (k.startsWith('map_')) {{
                        try {{
                            window[k].setMaxBounds({bounds_js});
                        }} catch(e){{}}
                    }}
                }}
            }}, 500);
        }});
        </script>
        """)
        m.get_root().html.add_child(script)

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
                folium.GeoJson(route, style_function=lambda x: {"color": "green", "weight": 4}).add_to(m)
                distance = round(data["routes"][0]["distance"] / 1000, 2)
                duration = round(data["routes"][0]["duration"] / 60, 1)
                st.success(f"🚶 Distance: **{distance} km** | ⏱ Time: **{duration} mins**")
        except requests.exceptions.RequestException:
            st.warning("⚠️ Could not fetch route.")

        # Show map
        st_folium(m, width=750, height=520)

        # Footer
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
