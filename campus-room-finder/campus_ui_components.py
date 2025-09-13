# campus_ui_components.py
"""
Campus Room Finder - Enhanced Mobile-First User Interface Components

This module contains all the Streamlit UI components and map visualization logic
for the campus room finder application with modern, responsive design matching
MUT brand colors and mobile-first approach.
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval
from branca.element import Element
from typing import List, Optional, Dict, Any
import base64
from pathlib import Path

from campus_data_logic import (
    Room, UserLocation, RouteInfo, GeometryUtils, 
    DataLoader, RoomSearchEngine, RouteCalculator, 
    AccessController, Config
)


class MUTTheme:
    """MUT University brand colors and styling constants."""
    
    # Primary brand colors from MUT website
    PRIMARY_RED = "#D32F2F"
    PRIMARY_GREEN = "#4CAF50"
    ACCENT_BLUE = "#2196F3"
    
    # Supporting colors
    DARK_GRAY = "#2C3E50"
    LIGHT_GRAY = "#F5F5F5"
    WHITE = "#FFFFFF"
    TEXT_DARK = "#333333"
    TEXT_LIGHT = "#666666"
    
    # Gradient colors
    GRADIENT_PRIMARY = "linear-gradient(135deg, #D32F2F, #B71C1C)"
    GRADIENT_SECONDARY = "linear-gradient(135deg, #4CAF50, #388E3C)"
    GRADIENT_ACCENT = "linear-gradient(135deg, #2196F3, #1976D2)"
    
    @classmethod
    def get_custom_css(cls) -> str:
        """Get comprehensive CSS styling for the application."""
        return f"""
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        /* Global Styles */
        .main .block-container {{
            padding-top: 0rem;
            padding-bottom: 2rem;
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 100%;
        }}
        
        /* Hide Streamlit branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}
        
        /* Main app container */
        .stApp {{
            background: {cls.LIGHT_GRAY};
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}
        
        /* Header Styling */
        .mut-header {{
            background: {cls.GRADIENT_PRIMARY};
            padding: 1rem 1.5rem;
            border-radius: 0 0 24px 24px;
            margin: -1rem -1rem 2rem -1rem;
            color: white;
            box-shadow: 0 4px 20px rgba(211, 47, 47, 0.3);
            position: relative;
            overflow: hidden;
        }}
        
        .mut-header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="2" fill="white" opacity="0.1"/><circle cx="20" cy="20" r="1" fill="white" opacity="0.1"/><circle cx="80" cy="30" r="1.5" fill="white" opacity="0.1"/></svg>');
            pointer-events: none;
        }}
        
        .header-content {{
            display: flex;
            align-items: center;
            gap: 1rem;
            position: relative;
            z-index: 2;
        }}
        
        .mut-logo {{
            width: 50px;
            height: 50px;
            background: white;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            color: {cls.PRIMARY_RED};
            font-size: 1.2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            flex-shrink: 0;
        }}
        
        .header-text {{
            flex: 1;
        }}
        
        .header-title {{
            font-size: 1.5rem;
            font-weight: 700;
            margin: 0;
            line-height: 1.2;
        }}
        
        .header-subtitle {{
            font-size: 0.9rem;
            opacity: 0.9;
            margin: 0;
            font-weight: 400;
        }}
        
        /* Mobile-First Search Section */
        .search-container {{
            background: white;
            border-radius: 16px;
            padding: 1rem;
            margin: 1rem 0;
            box-shadow: 0 2px 15px rgba(0,0,0,0.1);
            border: 1px solid #E0E0E0;
        }}
        
        .search-container .stTextInput > div > div > input {{
            border: 2px solid #E0E0E0;
            border-radius: 12px;
            padding: 0.75rem 1rem 0.75rem 2.5rem;
            font-size: 1rem;
            transition: all 0.3s ease;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" fill="%23666" viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>') no-repeat 12px center;
            background-size: 20px;
        }}
        
        .search-container .stTextInput > div > div > input:focus {{
            border-color: {cls.PRIMARY_RED};
            box-shadow: 0 0 0 3px rgba(211, 47, 47, 0.1);
            outline: none;
        }}
        
        /* Map Style Selector */
        .map-style-container {{
            background: white;
            border-radius: 16px;
            padding: 1rem;
            margin: 1rem 0;
            box-shadow: 0 2px 15px rgba(0,0,0,0.1);
        }}
        
        .map-style-container .stSelectbox > div > div {{
            border: 2px solid #E0E0E0;
            border-radius: 12px;
            transition: all 0.3s ease;
        }}
        
        .map-style-container .stSelectbox > div > div:focus-within {{
            border-color: {cls.PRIMARY_RED};
            box-shadow: 0 0 0 3px rgba(211, 47, 47, 0.1);
        }}
        
        /* Room Details Card */
        .room-card {{
            background: white;
            border-radius: 20px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border-left: 5px solid {cls.PRIMARY_RED};
            position: relative;
            overflow: hidden;
        }}
        
        .room-card::before {{
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            width: 100px;
            height: 100px;
            background: {cls.GRADIENT_PRIMARY};
            opacity: 0.1;
            border-radius: 50%;
            transform: translate(30px, -30px);
        }}
        
        .room-header {{
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
            position: relative;
            z-index: 2;
        }}
        
        .room-icon {{
            width: 60px;
            height: 60px;
            background: {cls.GRADIENT_PRIMARY};
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.5rem;
            box-shadow: 0 4px 15px rgba(211, 47, 47, 0.3);
        }}
        
        .room-title {{
            font-size: 1.5rem;
            font-weight: 700;
            color: {cls.TEXT_DARK};
            margin: 0;
            line-height: 1.2;
        }}
        
        .room-subtitle {{
            color: {cls.TEXT_LIGHT};
            font-size: 0.9rem;
            margin: 0.25rem 0 0 0;
        }}
        
        .room-details {{
            display: grid;
            gap: 1rem;
            position: relative;
            z-index: 2;
        }}
        
        .detail-item {{
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            background: {cls.LIGHT_GRAY};
            border-radius: 12px;
            transition: all 0.3s ease;
        }}
        
        .detail-item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .detail-icon {{
            width: 40px;
            height: 40px;
            background: {cls.GRADIENT_ACCENT};
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.1rem;
            flex-shrink: 0;
        }}
        
        .detail-text {{
            flex: 1;
        }}
        
        .detail-label {{
            font-weight: 600;
            color: {cls.TEXT_DARK};
            font-size: 0.9rem;
        }}
        
        .detail-value {{
            color: {cls.TEXT_LIGHT};
            font-size: 0.85rem;
            margin-top: 0.25rem;
        }}
        
        /* Status Messages */
        .status-card {{
            border-radius: 16px;
            padding: 1rem 1.5rem;
            margin: 1rem 0;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            font-weight: 500;
            animation: slideInUp 0.5s ease;
        }}
        
        .status-loading {{
            background: linear-gradient(135deg, #FF9800, #F57C00);
            color: white;
        }}
        
        .status-success {{
            background: {cls.GRADIENT_SECONDARY};
            color: white;
        }}
        
        .status-info {{
            background: {cls.GRADIENT_ACCENT};
            color: white;
        }}
        
        .status-error {{
            background: linear-gradient(135deg, #F44336, #D32F2F);
            color: white;
        }}
        
        /* Route Statistics */
        .route-stats {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin: 1rem 0;
        }}
        
        .stat-card {{
            background: white;
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        }}
        
        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: {cls.GRADIENT_PRIMARY};
        }}
        
        .stat-value {{
            font-size: 2rem;
            font-weight: 800;
            color: {cls.PRIMARY_RED};
            margin-bottom: 0.5rem;
            line-height: 1;
        }}
        
        .stat-label {{
            color: {cls.TEXT_LIGHT};
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        /* Suggestion Buttons */
        .suggestion-btn {{
            background: white;
            border: 2px solid #E0E0E0;
            border-radius: 12px;
            padding: 0.75rem 1rem;
            margin: 0.25rem;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
            color: {cls.TEXT_DARK};
            display: inline-block;
            text-decoration: none;
        }}
        
        .suggestion-btn:hover {{
            border-color: {cls.PRIMARY_RED};
            background: {cls.PRIMARY_RED};
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(211, 47, 47, 0.3);
        }}
        
        /* Footer */
        .mut-footer {{
            background: {cls.DARK_GRAY};
            color: white;
            padding: 2rem;
            border-radius: 20px 20px 0 0;
            margin: 2rem -1rem 0 -1rem;
            text-align: center;
        }}
        
        .footer-brand {{
            font-size: 1.2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        
        .footer-tech {{
            color: {cls.PRIMARY_GREEN};
            font-weight: 800;
        }}
        
        .footer-attribution {{
            font-size: 0.85rem;
            opacity: 0.8;
            margin-top: 1rem;
            line-height: 1.5;
        }}
        
        /* Responsive Design */
        @media (min-width: 768px) {{
            .main .block-container {{
                padding-left: 2rem;
                padding-right: 2rem;
                max-width: 1200px;
                margin: 0 auto;
            }}
            
            .mut-header {{
                margin: -2rem -2rem 2rem -2rem;
                padding: 2rem 2.5rem;
            }}
            
            .header-title {{
                font-size: 2rem;
            }}
            
            .header-subtitle {{
                font-size: 1rem;
            }}
            
            .mut-logo {{
                width: 70px;
                height: 70px;
                font-size: 1.5rem;
            }}
            
            .desktop-layout {{
                display: grid;
                grid-template-columns: 1fr 2fr;
                gap: 2rem;
                align-items: start;
            }}
            
            .route-stats {{
                grid-template-columns: 1fr 1fr;
            }}
            
            .mut-footer {{
                margin: 2rem -2rem 0 -2rem;
            }}
        }}
        
        /* Animations */
        @keyframes slideInUp {{
            from {{ opacity: 0; transform: translateY(30px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
        }}
        
        .pulse {{ animation: pulse 2s infinite; }}
        
        /* Loading Animation */
        .loading-spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {cls.PRIMARY_RED};
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: #B71C1C;
        }}
        </style>
        """


class MapStyleManager:
    """Manages different map tile styles and their configurations."""
    
    TILE_LAYERS = {
        "🗺️ Standard": "OpenStreetMap",
        "🏔️ Terrain": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
        "🌙 Light": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png",
        "🌚 Dark": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}{r}.png",
        "🛰️ Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    }
    
    ATTRIBUTIONS = {
        "🗺️ Standard": "© OpenStreetMap contributors",
        "🏔️ Terrain": "Map tiles by Stamen Design, © OpenStreetMap",
        "🌙 Light": "© OpenStreetMap contributors © CARTO",
        "🌚 Dark": "© OpenStreetMap contributors © CARTO",
        "🛰️ Satellite": "Tiles © Esri — Source: Esri, DigitalGlobe and others"
    }
    
    @classmethod
    def get_tile_layer(cls, style: str) -> str:
        """Get the tile layer URL for a given map style."""
        return cls.TILE_LAYERS.get(style, cls.TILE_LAYERS["🗺️ Standard"])
    
    @classmethod
    def get_attribution(cls, style: str) -> str:
        """Get the attribution text for a given map style."""
        return cls.ATTRIBUTIONS.get(style, cls.ATTRIBUTIONS["🗺️ Standard"])


class UIComponents:
    """Collection of reusable UI components for the campus room finder."""
    
    @staticmethod
    def render_header() -> None:
        """Render the modern MUT-branded header with logo."""
        st.markdown(
            """
            <div class="mut-header">
                <div class="header-content">
                    <div class="mut-logo">
                        MUT
                    </div>
                    <div class="header-text">
                        <h1 class="header-title">Campus Room Finder</h1>
                        <p class="header-subtitle">Find your way around MUT campus with ease</p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    @staticmethod
    def render_search_container() -> None:
        """Render the styled search input container."""
        st.markdown('<div class="search-container">', unsafe_allow_html=True)
    
    @staticmethod
    def close_search_container() -> None:
        """Close the search input container."""
        st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def render_map_style_container() -> None:
        """Render the styled map style selector container."""
        st.markdown('<div class="map-style-container">', unsafe_allow_html=True)
    
    @staticmethod
    def close_map_style_container() -> None:
        """Close the map style selector container."""
        st.markdown('</div>', unsafe_allow_html=True)
    
    @staticmethod
    def render_room_details(room: Room) -> None:
        """
        Render room details in a modern card format.
        
        Args:
            room: Room object containing room information
        """
        st.markdown(
            f"""
            <div class="room-card">
                <div class="room-header">
                    <div class="room-icon">
                        🚪
                    </div>
                    <div>
                        <h3 class="room-title">{room.room_name}</h3>
                        <p class="room-subtitle">{room.building}</p>
                    </div>
                </div>
                <div class="room-details">
                    <div class="detail-item">
                        <div class="detail-icon">🏢</div>
                        <div class="detail-text">
                            <div class="detail-label">Building</div>
                            <div class="detail-value">{room.building}</div>
                        </div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-icon">🛗</div>
                        <div class="detail-text">
                            <div class="detail-label">Floor</div>
                            <div class="detail-value">{room.floor}</div>
                        </div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-icon">📍</div>
                        <div class="detail-text">
                            <div class="detail-label">Coordinates</div>
                            <div class="detail-value">{room.lat:.3f}, {room.lon:.3f}</div>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    @staticmethod
    def render_status_message(message: str, status_type: str = "info") -> None:
        """
        Render status message with appropriate styling.
        
        Args:
            message: Status message text
            status_type: Type of status (loading, success, info, error)
        """
        icon_map = {
            "loading": "🔄",
            "success": "✅",
            "info": "ℹ️",
            "error": "❌"
        }
        
        icon = icon_map.get(status_type, "ℹ️")
        
        st.markdown(
            f"""
            <div class="status-card status-{status_type}">
                <span class="{'loading-spinner' if status_type == 'loading' else ''}">{icon}</span>
                <span>{message}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    @staticmethod
    def render_route_stats(route: RouteInfo) -> None:
        """
        Render route statistics in card format.
        
        Args:
            route: RouteInfo object containing route data
        """
        st.markdown(
            f"""
            <div class="route-stats">
                <div class="stat-card">
                    <div class="stat-value">{route.distance_km}</div>
                    <div class="stat-label">KM</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{route.duration_minutes}</div>
                    <div class="stat-label">MINS</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    @staticmethod
    def render_suggestions(suggestions: List[str]) -> Optional[str]:
        """
        Render search suggestions as styled buttons.
        
        Args:
            suggestions: List of room name suggestions
            
        Returns:
            Selected room name, or None if no selection
        """
        if not suggestions:
            return None
        
        st.markdown("**💡 Suggestions:**")
        
        cols = st.columns(min(len(suggestions), 3))
        
        for i, room_name in enumerate(suggestions[:6]):  # Limit to 6 suggestions
            col = cols[i % 3]
            with col:
                if st.button(f"➡️ {room_name}", key=f"suggestion_{i}", use_container_width=True):
                    return room_name
        
        return None
    
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
            <div class="mut-footer">
                <div class="footer-brand">
                    🚀 Made with ❤️ by <span class="footer-tech">MUT TECH CLUB</span>
                </div>
                <p style="margin: 0.5rem 0; opacity: 0.9;">
                    Empowering students through innovative technology solutions
                </p>
                <div class="footer-attribution">
                    🗺️ Map style: <strong>{map_style}</strong><br>
                    {attribution}
                </div>
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
    """Handles creation and rendering of interactive maps with MUT styling."""
    
    def __init__(self, map_style: str = "🗺️ Standard"):
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
        
        # Create base map with MUT styling
        m = folium.Map(
            location=[user_location.lat, user_location.lon],
            zoom_start=Config.DEFAULT_ZOOM,
            tiles=tile_layer,
            attr=attribution,
            control_scale=True,
            max_bounds=True,
            prefer_canvas=True
        )
        
        # Add campus boundary with MUT colors
        self._add_campus_boundary(m, campus_boundary)
        
        # Set map bounds to campus area
        m.fit_bounds(bounds)
        
        # Add custom CSS styling to map
        self._add_map_styling(m)
        
        return m
    
    def _add_campus_boundary(self, 
                           map_obj: folium.Map, 
                           boundary: List[tuple]) -> None:
        """
        Add campus boundary polygon with MUT branding colors.
        
        Args:
            map_obj: Folium map object to add boundary to
            boundary: List of (lat, lon) tuples defining boundary
        """
        folium.Polygon(
            locations=[(lat, lon) for lat, lon in boundary],
            color=MUTTheme.PRIMARY_RED,
            weight=3,
            fill=True,
            fill_color=MUTTheme.PRIMARY_GREEN,
            fill_opacity=0.2,
            tooltip="🏫 MUT Campus Boundary"
        ).add_to(map_obj)
    
    def _add_map_styling(self, map_obj: folium.Map) -> None:
        """
        Add custom CSS styling to the map.
        
        Args:
            map_obj: Folium map object to style
        """
        custom_css = """
        <style>
        .leaflet-container {
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .leaflet-popup-content-wrapper {
            border-radius: 12px;
            font-family: 'Inter', sans-serif;
        }
        .leaflet-popup-tip {
            background: white;
        }
        </style>
        """
        
        map_obj.get_root().html.add_child(Element(custom_css))
    
    def add_markers(self, 
                   map_obj: folium.Map,
                   user_location: UserLocation,
                   room: Room) -> None:
        """
        Add user and room markers with custom styling.
        
        Args:
            map_obj: Folium map object to add markers to
            user_location: User's GPS coordinates
            room: Room object with location information
        """
        # User location marker with MUT blue styling
        folium.Marker(
            [user_location.lat, user_location.lon],
            tooltip="📍 You are here",
            popup=folium.Popup("Your current location", max_width=200),
            icon=folium.Icon(
                color="blue", 
                icon="user", 
                prefix="fa"
            )
        ).add_to(map_obj)
        
        # Room location marker with MUT red styling
        if room.lat and room.lon:
            folium.Marker(
                [room.lat, room.lon],
                tooltip=f"🎯 {room.room_name}",
                popup=folium.Popup(
                    f"""
                    <div style="font-family: Inter, sans-serif; text-align: center; padding: 10px;">
                        <h4 style="margin: 0 0 10px 0; color: #D32F2F;">🎯 {room.room_name}</h4>
                        <p style="margin: 0; color: #666;"><strong>Building:</strong> {room.building}</p>
                        <p style="margin: 0; color: #666;"><strong>Floor:</strong> {room.floor}</p>
                    </div>
                    """,
                    max_width=250
                ),
                icon=folium.Icon(
                    color="red", 
                    icon="map-marker", 
                    prefix="fa"
                )
            ).add_to(map_obj)
    
    def add_route(self, 
                 map_obj: folium.Map,
                 route: RouteInfo) -> None:
        """
        Add walking route with MUT-styled colors.
        
        Args:
            map_obj: Folium map object to add route to
            route: RouteInfo object containing route geometry
        """
        folium.GeoJson(
            route.geometry,
            style_function=lambda x: {
                "color": MUTTheme.PRIMARY_GREEN,
                "weight": 5,
                "opacity": 0.8,
                "dashArray": "10, 5"
            },
            tooltip="🚶 Walking Route to Destination"
        ).add_to(map_obj)


class SearchInterface:
    """Handles the room search user interface with modern mobile-first design."""
    
    def __init__(self, search_engine: RoomSearchEngine):
        """
        Initialize search interface with a search engine.
        
        Args:
            search_engine: RoomSearchEngine instance for performing searches
        """
        self.search_engine = search_engine
    
    def render_search_input(self) -> str:
        """
        Render modern search input field with styling.
        
        Returns:
            Current search query string
        """
        UIComponents.render_search_container()
        
        # Custom search input with placeholder
        search_query = st.text_input(
            "",
            placeholder="🔍 Search for rooms, buildings, labs...",
            help="Try searching for room numbers like 'A101' or building names like 'Library'",
            key="room_search"
        )
        
        UIComponents.close_search_container()
        
        return search_query
    
    def render_search_results(self, query: str) -> Optional[str]:
        """
        Render search results with modern suggestions interface.
        
        Args:
            query: Current search query
            
        Returns:
            Selected room name, or None if no selection made
        """
        if not query:
            return self._render_popular_rooms()
        
        # Get filtered rooms and suggestions
        filtered_rooms = self.search_engine.search(query)
        suggestions = self.search_engine.get_fuzzy_suggestions(query)
        
        # Show suggestions as modern buttons
        selected_room = UIComponents.render_suggestions(suggestions[:6])
        
        if selected_room:
            return selected_room
        
        # Show dropdown with all filtered results
        return self._render_results_dropdown(filtered_rooms)
    
    def _render_popular_rooms(self) -> Optional[str]:
        """
        Render popular/recent rooms when no search query.
        
        Returns:
            Selected room name, or None if no selection
        """
        popular_rooms = [
            "Library", "Cafeteria", "Auditorium", 
            "Computer Lab 1", "A101", "B205"
        ]
        
        st.markdown("**🔥 Popular Destinations:**")
        
        selected = UIComponents.render_suggestions(popular_rooms)
        
        if selected:
            return selected
            
        # Fallback dropdown for all rooms
        return self._render_all_rooms_dropdown()
    
    def _render_results_dropdown(self, rooms: List[Room]) -> Optional[str]:
        """
        Render dropdown selection for filtered rooms.
        
        Args:
            rooms: List of filtered Room objects
            
        Returns:
            Selected room name, or None if no rooms available
        """
        if not rooms:
            st.warning("🚫 No rooms found matching your search.")
            return None
            
        room_names = sorted(list(set(room.room_name for room in rooms)))
        
        if len(room_names) == 1:
            st.info(f"✨ Found: **{room_names[0]}**")
            return room_names[0]
        
        return st.selectbox(
            f"📋 Found {len(room_names)} rooms:",
            [""] + room_names,
            format_func=lambda x: "Select a room..." if x == "" else f"🎯 {x}"
        ) or None
    
    def _render_all_rooms_dropdown(self) -> Optional[str]:
        """
        Render dropdown with all available rooms.
        
        Returns:
            Selected room name, or None if no selection
        """
        all_room_names = sorted(list(set(room.room_name for room in self.search_engine.rooms)))
        
        selected = st.selectbox(
            "📋 Or select from all rooms:",
            [""] + all_room_names,
            format_func=lambda x: "Browse all rooms..." if x == "" else f"🏢 {x}"
        )
        
        return selected if selected else None


class CampusRoomFinderApp:
    """Main application class with modern mobile-first UI."""
    
    def __init__(self):
        """Initialize the enhanced campus room finder application."""
        # Configure Streamlit page with MUT branding
        st.set_page_config(
            page_title="MUT Campus Room Finder",
            page_icon="🎯",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Apply custom CSS styling
        st.markdown(MUTTheme.get_custom_css(), unsafe_allow_html=True)
        
        # Initialize session state for mobile navigation
        if 'current_section' not in st.session_state:
            st.session_state.current_section = 'search'
            
        if 'selected_room' not in st.session_state:
            st.session_state.selected_room = None
            
        if 'user_location' not in st.session_state:
            st.session_state.user_location = None
        
        # Load data
        try:
            self.rooms = DataLoader.load_rooms(Config.ROOMS_FILE)
            self.campus_boundary = DataLoader.load_campus_boundary(Config.BOUNDARIES_FILE)
        except Exception as e:
            st.error(f"❌ Error loading data: {str(e)}")
            st.stop()
        
        # Initialize components
        self.search_engine = RoomSearchEngine(self.rooms)
        self.access_controller = AccessController(self.campus_boundary)
        
        # Calculate campus bounds for map restrictions
        if self.campus_boundary:
            self.campus_bounds = GeometryUtils.calculate_bounding_box(self.campus_boundary)
        else:
            self.campus_bounds = [[-1.0, 36.0], [0.0, 38.0]]  # Default Kenya bounds
    
    def run(self) -> None:
        """Run the main application with modern mobile-first UI."""
        # Render header
        UIComponents.render_header()
        
        # Check if boundary data is available
        if not self.campus_boundary:
            st.error("❌ Campus boundary data not found. Please contact the administrator.")
            st.info("📄 Required file: `campus-room-finder/boundaries.csv`")
            st.stop()
        
        # Handle GPS and access control
        user_location = self._handle_access_control()
        
        # Main app layout
        self._render_main_interface(user_location)
    
    def _handle_access_control(self) -> UserLocation:
        """
        Handle GPS acquisition and access control with user-friendly messages.
        
        Returns:
            UserLocation object (with fallback to campus center)
        """
        # Show GPS status
        with st.spinner("📍 Getting your location..."):
            user_location = GPSManager.get_user_location()
        
        if user_location:
            # Validate location access
            is_valid, error_message = self.access_controller.is_location_valid(user_location)
            
            if not is_valid:
                UIComponents.render_status_message(
                    "⚠️ You appear to be outside campus. Showing campus center instead.",
                    "info"
                )
                # Fallback to campus center
                user_location = UserLocation(lat=-0.748, lon=37.150)
            else:
                UIComponents.render_status_message(
                    "✅ Location detected successfully!",
                    "success"
                )
        else:
            UIComponents.render_status_message(
                "📍 Using campus center as your starting location",
                "info"
            )
            # Default campus center
            user_location = UserLocation(lat=-0.748, lon=37.150)
        
        st.session_state.user_location = user_location
        return user_location
    
    def _render_main_interface(self, user_location: UserLocation) -> None:
        """
        Render the main application interface with responsive design.
        
        Args:
            user_location: User's GPS coordinates
        """
        # Map style selector
        UIComponents.render_map_style_container()
        map_style = st.selectbox(
            "🗺️ Choose Map Style:",
            list(MapStyleManager.TILE_LAYERS.keys()),
            help="Select your preferred map visualization style"
        )
        UIComponents.close_map_style_container()
        
        # Create responsive layout
        col1, col2 = st.columns([1, 2])
        
        with col1:
            self._render_search_section()
            
        with col2:
            self._render_map_section(user_location, map_style)
    
    def _render_search_section(self) -> None:
        """Render the search and room details section."""
        search_interface = SearchInterface(self.search_engine)
        
        # Search input
        search_query = search_interface.render_search_input()
        
        # Search results
        selected_room_name = search_interface.render_search_results(search_query)
        
        if selected_room_name:
            # Find the room object
            selected_room = next(
                (room for room in self.rooms if room.room_name == selected_room_name), 
                None
            )
            
            if selected_room:
                st.session_state.selected_room = selected_room
                
                # Display room details
                UIComponents.render_room_details(selected_room)
                
                # Show route calculation status
                if st.session_state.user_location:
                    self._calculate_and_display_route(selected_room)
            else:
                st.error("❌ Room data not found. Please try again.")
        else:
            # Show welcome message when no room selected
            st.markdown(
                """
                <div style="text-align: center; padding: 2rem; color: #666;">
                    <h3>🎯 Welcome to MUT Campus</h3>
                    <p>Search for any room, lab, or facility to get instant directions with walking routes.</p>
                    <p><strong>Popular searches:</strong> Library, Cafeteria, Computer Lab, Auditorium</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    def _calculate_and_display_route(self, room: Room) -> None:
        """
        Calculate and display route information.
        
        Args:
            room: Selected Room object
        """
        if not room.lat or not room.lon:
            UIComponents.render_status_message(
                "❌ Room location coordinates not available",
                "error"
            )
            return
        
        user_location = st.session_state.user_location
        
        # Show loading state
        UIComponents.render_status_message(
            "🔄 Calculating optimal walking route...",
            "loading"
        )
        
        # Calculate route
        route = RouteCalculator.get_walking_route(
            user_location.lat, user_location.lon,
            room.lat, room.lon,
            timeout=Config.ROUTE_TIMEOUT
        )
        
        if route:
            UIComponents.render_status_message(
                "✅ Route calculated successfully!",
                "success"
            )
            UIComponents.render_route_stats(route)
        else:
            UIComponents.render_status_message(
                "⚠️ Could not calculate route. Showing direct path instead.",
                "error"
            )
    
    def _render_map_section(self, user_location: UserLocation, map_style: str) -> None:
        """
        Render the interactive map section.
        
        Args:
            user_location: User's GPS coordinates
            map_style: Selected map style
        """
        selected_room = st.session_state.get('selected_room')
        
        if selected_room and selected_room.lat and selected_room.lon:
            # Create and configure map
            map_renderer = MapRenderer(map_style)
            campus_map = map_renderer.create_campus_map(
                user_location, 
                self.campus_boundary, 
                self.campus_bounds
            )
            
            # Add markers
            map_renderer.add_markers(campus_map, user_location, selected_room)
            
            # Add route if available
            route = RouteCalculator.get_walking_route(
                user_location.lat, user_location.lon,
                selected_room.lat, selected_room.lon,
                timeout=Config.ROUTE_TIMEOUT
            )
            
            if route:
                map_renderer.add_route(campus_map, route)
            
            # Display the map
            st_folium(campus_map, width=None, height=500, returned_objects=[])
            
        else:
            # Show campus overview map
            map_renderer = MapRenderer(map_style)
            campus_map = map_renderer.create_campus_map(
                user_location, 
                self.campus_boundary, 
                self.campus_bounds
            )
            
            # Add only user marker
            folium.Marker(
                [user_location.lat, user_location.lon],
                tooltip="📍 You are here",
                icon=folium.Icon(color="blue", icon="user", prefix="fa")
            ).add_to(campus_map)
            
            st_folium(campus_map, width=None, height=500, returned_objects=[])
            
            st.markdown(
                """
                <div style="text-align: center; padding: 1rem; background: white; 
                           border-radius: 16px; margin-top: 1rem; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <h4 style="color: #D32F2F; margin: 0;">🗺️ MUT Campus Map</h4>
                    <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">
                        Select a room to see the route and get directions
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Render footer
        UIComponents.render_footer(map_style)


def main():
    """Main entry point for the enhanced MUT Campus Room Finder application."""
    try:
        app = CampusRoomFinderApp()
        app.run()
    except Exception as e:
        st.error(f"❌ Application Error: {str(e)}")
        st.info("🔄 Please refresh the page or contact support if the problem persists.")
        
        # Show error details in expander for debugging
        with st.expander("🔧 Technical Details"):
            st.exception(e)


if __name__ == "__main__":
    main()