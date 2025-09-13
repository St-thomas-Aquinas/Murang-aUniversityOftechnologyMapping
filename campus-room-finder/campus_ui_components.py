# campus_ui_components.py
"""
Campus Room Finder - User Interface Components

This module contains all the Streamlit UI components and map visualization logic
for the campus room finder application. It's separated from the business logic
to maintain clean separation of concerns.
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
from branca.element import Element
from typing import List, Optional, Dict, Any

from campus_data_logic import (
    Room, UserLocation, RouteInfo, GeometryUtils, 
    DataLoader, RoomSearchEngine, RouteCalculator, 
    AccessController, Config
)


class MapStyleManager:
    """Manages different map tile styles and their configurations."""
    
    TILE_LAYERS = {
        "Standard": "OpenStreetMap",
        "Terrain": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
        "Light": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png",
        "Dark": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}{r}.png",
        "Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    }
    
    ATTRIBUTIONS = {
        "Standard": "© OpenStreetMap contributors",
        "Terrain": "Map tiles by Stamen Design, © OpenStreetMap",
        "Light": "© OpenStreetMap contributors © CARTO",
        "Dark": "© OpenStreetMap contributors © CARTO",
        "Satellite": "Tiles © Esri — Source: Esri, DigitalGlobe and others"
    }
    
    @classmethod
    def get_tile_layer(cls, style: str) -> str:
        """Get the tile layer URL for a given map style."""
        return cls.TILE_LAYERS.get(style, cls.TILE_LAYERS["Standard"])
    
    @classmethod
    def get_attribution(cls, style: str) -> str:
        """Get the attribution text for a given map style."""
        return cls.ATTRIBUTIONS.get(style, cls.ATTRIBUTIONS["Standard"])


class UIComponents:
    """Collection of reusable UI components for the campus room finder."""
    
    @staticmethod
    def render_error_page(error_code: str, title: str, message: str) -> None:
        """
        Render a full-page error message with custom styling.
        
        Args:
            error_code: HTTP-style error code (e.g., "403", "404")
            title: Error title text
            message: Detailed error message
        """
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; justify-content:center; 
                       height:70vh; flex-direction:column;">
                <h1 style="font-size:96px; margin:0;">{error_code}</h1>
                <h2 style="font-size:28px; margin:0;">{title}</h2>
                <p style="color:gray; max-width:700px; text-align:center;">
                    {message}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    @staticmethod
    def render_room_details(room: Room) -> None:
        """
        Render room details in a styled card format.
        
        Args:
            room: Room object containing room information
        """
        st.markdown(
            f"""
            <div style="padding:15px; background:#f9f9f9; border-radius:10px;">
                <h3>📍 {room.room_name}</h3>
                <p>🏢 Building: <b>{room.building}</b></p>
                <p>🛗 Floor: <b>{room.floor}</b></p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    @staticmethod
    def render_route_info(route: RouteInfo) -> None:
        """
        Render route information with distance and duration.
        
        Args:
            route: RouteInfo object containing route data
        """
        st.success(
            f"🚶 Distance: **{route.distance_km} km** | "
            f"⏱ Time: **{route.duration_minutes} mins**"
        )
    
    @staticmethod
    def render_footer(map_style: str) -> None:
        """
        Render application footer with credits and map attribution.
        
        Args:
            map_style: Current map style name
        """
        attribution = MapStyleManager.get_attribution(map_style)
        st.markdown(
            f"""
            <div style="text-align:center; font-size:12px; color:gray; margin-top:5px;">
                🗺️ Map style: <b>{map_style}</b> <br>
                {attribution} <br><br>
                <span style="font-size:16px; font-weight:bold; color:#228B22;">
                    🚀 Made by <span style="color:#FFD700;">MUT TECH CLUB</span>
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )


class GPSManager:
    """Handles GPS location acquisition using JavaScript evaluation."""
    
    @staticmethod
    def get_user_location() -> Optional[UserLocation]:
        """
        Get user's current GPS location using browser geolocation API.
        
        Returns:
            UserLocation object with coordinates, or None if unavailable
        """
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
        
        if user_coords and 'lat' in user_coords and 'lon' in user_coords:
            return UserLocation(
                lat=user_coords['lat'],
                lon=user_coords['lon']
            )
        return None


class MapRenderer:
    """Handles creation and rendering of interactive maps."""
    
    def __init__(self, map_style: str = "Standard"):
        """
        Initialize map renderer with specified style.
        
        Args:
            map_style: Map tile style name
        """
        self.map_style = map_style
    
    def create_campus_map(self, 
                         user_location: UserLocation,
                         campus_boundary: List[tuple],
                         bounds: List[List[float]]) -> folium.Map:
        """
        Create a base map centered on user location with campus boundary.
        
        Args:
            user_location: User's GPS coordinates
            campus_boundary: Campus polygon boundary points
            bounds: Bounding box for map restrictions
            
        Returns:
            Configured folium Map object
        """
        tile_layer = MapStyleManager.get_tile_layer(self.map_style)
        attribution = MapStyleManager.get_attribution(self.map_style)
        
        # Create base map
        m = folium.Map(
            location=[user_location.lat, user_location.lon],
            zoom_start=Config.DEFAULT_ZOOM,
            tiles=tile_layer,
            attr=attribution,
            control_scale=True,
            max_bounds=True
        )
        
        # Add campus boundary polygon
        self._add_campus_boundary(m, campus_boundary)
        
        # Set map bounds to campus area
        m.fit_bounds(bounds)
        
        # Add JavaScript to enforce map bounds
        self._add_bounds_restriction(m, bounds)
        
        return m
    
    def _add_campus_boundary(self, 
                           map_obj: folium.Map, 
                           boundary: List[tuple]) -> None:
        """
        Add campus boundary polygon to the map.
        
        Args:
            map_obj: Folium map object to add boundary to
            boundary: List of (lat, lon) tuples defining boundary
        """
        folium.Polygon(
            locations=[(lat, lon) for lat, lon in boundary],
            color=Config.CAMPUS_BOUNDARY_COLOR,
            weight=Config.CAMPUS_BOUNDARY_WEIGHT,
            fill=True,
            fill_opacity=Config.CAMPUS_BOUNDARY_OPACITY,
            tooltip="MUT Campus Boundary"
        ).add_to(map_obj)
    
    def _add_bounds_restriction(self, 
                              map_obj: folium.Map, 
                              bounds: List[List[float]]) -> None:
        """
        Add JavaScript to restrict map panning to campus bounds.
        
        Args:
            map_obj: Folium map object to restrict
            bounds: Bounding box coordinates
        """
        min_lat, min_lon = bounds[0]
        max_lat, max_lon = bounds[1]
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
        
        map_obj.get_root().html.add_child(script)
    
    def add_markers(self, 
                   map_obj: folium.Map,
                   user_location: UserLocation,
                   room: Room) -> None:
        """
        Add user and room markers to the map.
        
        Args:
            map_obj: Folium map object to add markers to
            user_location: User's GPS coordinates
            room: Room object with location information
        """
        # User location marker (blue)
        folium.Marker(
            [user_location.lat, user_location.lon],
            tooltip="You are here",
            icon=folium.Icon(color="blue")
        ).add_to(map_obj)
        
        # Room location marker (red)
        if room.lat and room.lon:
            folium.Marker(
                [room.lat, room.lon],
                tooltip=room.room_name,
                icon=folium.Icon(color="red")
            ).add_to(map_obj)
    
    def add_route(self, 
                 map_obj: folium.Map,
                 route: RouteInfo) -> None:
        """
        Add walking route to the map.
        
        Args:
            map_obj: Folium map object to add route to
            route: RouteInfo object containing route geometry
        """
        folium.GeoJson(
            route.geometry,
            style_function=lambda x: {
                "color": Config.ROUTE_COLOR,
                "weight": Config.ROUTE_WEIGHT
            }
        ).add_to(map_obj)


class SearchInterface:
    """Handles the room search user interface components."""
    
    def __init__(self, search_engine: RoomSearchEngine):
        """
        Initialize search interface with a search engine.
        
        Args:
            search_engine: RoomSearchEngine instance for performing searches
        """
        self.search_engine = search_engine
    
    def render_search_input(self) -> str:
        """
        Render search input field.
        
        Returns:
            Current search query string
        """
        return st.text_input("🔍 Search for a room by name:")
    
    def render_search_results(self, query: str) -> Optional[str]:
        """
        Render search results with suggestions and selection interface.
        
        Args:
            query: Current search query
            
        Returns:
            Selected room name, or None if no selection made
        """
        if not query:
            return self._render_fallback_dropdown(self.search_engine.rooms)
        
        # Get filtered rooms based on search
        filtered_rooms = self.search_engine.search(query)
        
        # Show fuzzy suggestions as clickable buttons
        suggestions = self.search_engine.get_fuzzy_suggestions(query)
        selected_room = self._render_suggestions(suggestions)
        
        if selected_room:
            return selected_room
        
        # Show dropdown with filtered results
        return self._render_fallback_dropdown(filtered_rooms)
    
    def _render_suggestions(self, suggestions: List[str]) -> Optional[str]:
        """
        Render clickable suggestion buttons.
        
        Args:
            suggestions: List of room name suggestions
            
        Returns:
            Selected room name, or None if no button clicked
        """
        if not suggestions:
            return None
            
        st.write("Suggestions:")
        for room_name in sorted(suggestions):
            if st.button(f"➡ {room_name}"):
                return room_name
        
        return None
    
    def _render_fallback_dropdown(self, rooms: List[Room]) -> Optional[str]:
        """
        Render fallback dropdown selection for rooms.
        
        Args:
            rooms: List of Room objects to display
            
        Returns:
            Selected room name, or None if no rooms available
        """
        if not rooms:
            return None
            
        room_names = sorted({room.room_name for room in rooms})
        return st.selectbox("Select a room:", room_names)


class CampusRoomFinderApp:
    """Main application class that coordinates all UI components."""
    
    def __init__(self):
        """Initialize the campus room finder application."""
        # Configure Streamlit page
        st.set_page_config(layout="wide")
        
        # Load data
        self.rooms = DataLoader.load_rooms(Config.ROOMS_FILE)
        self.campus_boundary = DataLoader.load_campus_boundary(Config.BOUNDARIES_FILE)
        
        # Initialize components
        self.search_engine = RoomSearchEngine(self.rooms)
        self.access_controller = AccessController(self.campus_boundary)
        
        # Calculate campus bounds for map restrictions
        self.campus_bounds = GeometryUtils.calculate_bounding_box(self.campus_boundary)
    
    def run(self) -> None:
        """Run the main application flow."""
        st.title("MUT Campus Room Finder")
        
        # Check if boundary data is available
        if not self.campus_boundary:
            st.error("Campus boundary not found (campus-room-finder/boundaries.csv). Admin must provide it.")
            st.stop()
        
        # Get map style selection
        map_style = st.selectbox(
            "🗺️ Choose Map Style:",
            ["Standard", "Terrain", "Light", "Dark", "Satellite"]
        )
        
        # Handle GPS and access control
        user_location = self._handle_access_control()
        if not user_location:
            return
        
        # Handle room search and selection
        selected_room = self._handle_room_search()
        if not selected_room:
            st.warning("⚠️ No rooms found. Try another search.")
            return
        
        # Display room information and map
        self._display_room_and_map(selected_room, user_location, map_style)
    
    def _handle_access_control(self) -> Optional[UserLocation]:
        """
        Handle GPS acquisition and access control.
        
        Returns:
            UserLocation if access is granted, None otherwise
        """
        # Get user location (commented out GPS check for development)
        # user_location = GPSManager.get_user_location()
        user_location = None  # Temporary for testing
        
        # Check access permissions
        is_valid, error_message = self.access_controller.is_location_valid(user_location)
        
        if not is_valid:
            if user_location is None:
                UIComponents.render_error_page("403", "Access Denied", error_message)
            else:
                UIComponents.render_error_page("404", "Access Denied", error_message)
            st.stop()
            return None
        
        return user_location
    
    def _handle_room_search(self) -> Optional[Room]:
        """
        Handle room search interface and return selected room.
        
        Returns:
            Selected Room object, or None if no valid selection
        """
        search_interface = SearchInterface(self.search_engine)
        
        # Get search input
        search_query = search_interface.render_search_input()
        
        # Get selected room name
        selected_room_name = search_interface.render_search_results(search_query)
        
        if not selected_room_name:
            return None
        
        # Find and return the Room object
        return next((room for room in self.rooms if room.room_name == selected_room_name), None)
    
    def _display_room_and_map(self, 
                            room: Room, 
                            user_location: UserLocation, 
                            map_style: str) -> None:
        """
        Display selected room information and interactive map.
        
        Args:
            room: Selected Room object
            user_location: User's GPS coordinates
            map_style: Selected map style
        """
        if not room.lat or not room.lon:
            st.warning("⚠️ Selected room location data is not available.")
            return
        
        # Display room details
        UIComponents.render_room_details(room)
        
        # Create and configure map
        map_renderer = MapRenderer(map_style)
        campus_map = map_renderer.create_campus_map(
            user_location, 
            self.campus_boundary, 
            self.campus_bounds
        )
        
        # Add markers for user and room
        map_renderer.add_markers(campus_map, user_location, room)
        
        # Calculate and display route
        route = RouteCalculator.get_walking_route(
            user_location.lat, user_location.lon,
            room.lat, room.lon,
            timeout=Config.ROUTE_TIMEOUT
        )
        
        if route:
            map_renderer.add_route(campus_map, route)
            UIComponents.render_route_info(route)
        else:
            st.warning("⚠️ Could not fetch route.")
        
        # Display the map
        st_folium(campus_map, width=750, height=520)
        
        # Display footer
        UIComponents.render_footer(map_style)


def main():
    """Main entry point for the application."""
    app = CampusRoomFinderApp()
    app.run()


if __name__ == "__main__":
    main()
