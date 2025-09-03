# Build map (default Terrain)
m = folium.Map(location=[user_lat, user_lon], zoom_start=17, tiles=None)

# Base layers without attribution (attr="")
folium.TileLayer("OpenStreetMap", name="Standard", attr="").add_to(m)
folium.TileLayer(
    tiles="https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
    attr="",  # removed from map
    name="Terrain",
    control=True
).add_to(m)
folium.TileLayer(
    tiles="https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png",
    attr="",  # removed
    name="Light"
).add_to(m)
folium.TileLayer(
    tiles="https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}{r}.png",
    attr="",  # removed
    name="Dark"
).add_to(m)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="",  # removed
    name="Satellite"
).add_to(m)

# Add Layer Control (map type switcher)
folium.LayerControl().add_to(m)

# Show map
st_folium(m, width=750, height=520)

# Show attribution separately under the map
st.caption("🗺️ Map tiles © OpenStreetMap, Stamen, CARTO, Esri. Data © OpenStreetMap contributors")
