# campus_data_logic.py
"""
Campus Room Finder - Data Models and Business Logic

This module contains all the core business logic, data models, and utility functions
for the campus room finder application. It's separated from the UI to maintain
clean architecture and enable easier testing and maintenance.
"""

import json
import csv
import re
import requests
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from rapidfuzz import process


@dataclass
class Room:
    """Data model representing a campus room with all its properties."""
    room_name: str
    building: str
    floor: str
    lat: Optional[float]
    lon: Optional[float]
    
    def __post_init__(self):
        """Ensure floor is always a string and handle None values."""
        if self.floor is None:
            self.floor = ""
        else:
            self.floor = str(self.floor)


@dataclass
class UserLocation:
    """Data model representing user's GPS coordinates."""
    lat: float
    lon: float


@dataclass
class RouteInfo:
    """Data model representing route information between two points."""
    distance_km: float
    duration_minutes: float
    geometry: Dict[str, Any]


class GeometryUtils:
    """Utility class for geometric calculations and spatial operations."""
    
    @staticmethod
    def point_in_polygon(lat: float, lon: float, poly: List[Tuple[float, float]]) -> bool:
        """
        Determine if a point is inside a polygon using ray-casting algorithm.
        
        Args:
            lat: Latitude of the point to test
            lon: Longitude of the point to test
            poly: List of (lat, lon) tuples defining the polygon boundary
            
        Returns:
            bool: True if point is inside polygon, False otherwise
        """
        x = lon
        y = lat
        inside = False
        n = len(poly)
        
        if n == 0:
            return False
            
        j = n - 1
        for i in range(n):
            # poly stored as (lat, lon), so swap for x, y calculation
            xi, yi = poly[i][1], poly[i][0]
            xj, yj = poly[j][1], poly[j][0]
            
            # Check if ray from point intersects with polygon edge
            intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
            if intersect:
                inside = not inside
            j = i
            
        return inside
    
    @staticmethod
    def calculate_bounding_box(poly: List[Tuple[float, float]]) -> List[List[float]]:
        """
        Calculate the bounding box (min/max lat/lon) for a polygon.
        
        Args:
            poly: List of (lat, lon) tuples defining the polygon
            
        Returns:
            List of [[min_lat, min_lon], [max_lat, max_lon]]
        """
        if not poly:
            return [[0, 0], [0, 0]]
            
        lats = [pt[0] for pt in poly]
        lons = [pt[1] for pt in poly]
        
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        return [[min_lat, min_lon], [max_lat, max_lon]]


class DataLoader:
    """Handles loading and parsing of data files for the campus room finder."""
    
    @staticmethod
    def load_rooms(file_path: str = "campus-room-finder/rooms.json") -> List[Room]:
        """
        Load room data from JSON file and convert to Room objects.
        
        Args:
            file_path: Path to the rooms JSON file
            
        Returns:
            List of Room objects sorted by room name
        """
        try:
            p = Path(file_path)
            with p.open("r", encoding="utf-8") as f:
                rooms_data = json.load(f)
                
            rooms = []
            for room_data in rooms_data:
                room = Room(
                    room_name=room_data.get("room_name", ""),
                    building=room_data.get("building", ""),
                    floor=room_data.get("floor"),
                    lat=room_data.get("lat"),
                    lon=room_data.get("lon")
                )
                rooms.append(room)
                
            # Sort rooms by name for consistent ordering
            return sorted(rooms, key=lambda x: x.room_name.lower())
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Error loading rooms data: {e}")
            return []
    
    @staticmethod
    def load_campus_boundary(file_path: str = "campus-room-finder/boundaries.csv") -> List[Tuple[float, float]]:
        """
        Load campus boundary polygon from CSV file.
        
        Supports multiple formats:
        - WKT POINT format in 'WKT' column
        - Separate 'lat'/'lon' or 'latitude'/'longitude' columns
        - 'x'/'y' coordinate columns
        
        Args:
            file_path: Path to the boundaries CSV file
            
        Returns:
            List of (lat, lon) tuples defining the campus boundary polygon
        """
        poly = []
        p = Path(file_path)
        
        if not p.exists():
            print(f"Boundaries file not found: {file_path}")
            return []
            
        try:
            with p.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        lat, lon = DataLoader._parse_coordinate_row(row)
                        poly.append((lat, lon))
                    except (TypeError, ValueError) as e:
                        print(f"Skipping invalid coordinate row: {e}")
                        continue
                        
        except Exception as e:
            print(f"Error loading boundary data: {e}")
            
        print(f"Loaded {len(poly)} boundary points")
        return poly
    
    @staticmethod
    def _parse_coordinate_row(row: Dict[str, str]) -> Tuple[float, float]:
        """
        Parse a single row from the boundary CSV to extract coordinates.
        
        Args:
            row: Dictionary representing a CSV row
            
        Returns:
            Tuple of (lat, lon) coordinates
            
        Raises:
            ValueError: If coordinates cannot be parsed from the row
        """
        # Try parsing WKT format first
        wkt = (row.get("WKT") or row.get("wkt") or "").strip()
        if wkt:
            # Look for POINT(lon lat) format
            m = re.search(r"POINT\s*\(\s*(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*\)", wkt, re.IGNORECASE)
            if not m:
                # Fallback to any two decimal numbers
                m = re.search(r"(-?\d+\.\d+)[,\s]+(-?\d+\.\d+)", wkt)
            if m:
                # Note: WKT typically uses (lon, lat) format
                lon, lat = float(m.group(1)), float(m.group(2))
                return lat, lon
                
        # Try standard lat/lon columns
        lat = row.get("lat") or row.get("latitude") or row.get("y")
        lon = row.get("lon") or row.get("longitude") or row.get("x")
        
        if lat is None or lon is None:
            raise ValueError("No valid coordinates found in row")
            
        return float(lat), float(lon)


class RoomSearchEngine:
    """Handles room searching with both substring and fuzzy matching."""
    
    def __init__(self, rooms: List[Room]):
        """
        Initialize the search engine with a list of rooms.
        
        Args:
            rooms: List of Room objects to search through
        """
        self.rooms = rooms
        self.room_names = [room.room_name for room in rooms]
    
    def search(self, query: str, fuzzy_limit: int = 5, fuzzy_threshold: int = 60) -> List[Room]:
        """
        Search for rooms using both substring and fuzzy matching.
        
        Args:
            query: Search query string
            fuzzy_limit: Maximum number of fuzzy matches to return
            fuzzy_threshold: Minimum fuzzy match score (0-100)
            
        Returns:
            List of Room objects matching the search criteria
        """
        if not query:
            return self.rooms.copy()
            
        query_lower = query.lower()
        
        # Find substring matches (exact substring matching)
        substring_matches = [
            room for room in self.rooms 
            if query_lower in room.room_name.lower()
        ]
        
        # Find fuzzy matches using rapidfuzz
        fuzzy_matches = process.extract(
            query, 
            self.room_names, 
            limit=fuzzy_limit, 
            score_cutoff=fuzzy_threshold
        )
        
        # Get room objects for fuzzy matches
        fuzzy_names = {match[0] for match in fuzzy_matches}
        fuzzy_rooms = [
            room for room in self.rooms 
            if room.room_name in fuzzy_names
        ]
        
        # Combine results, removing duplicates
        combined_rooms = {room.room_name: room for room in (substring_matches + fuzzy_rooms)}
        
        # Return sorted results
        return sorted(combined_rooms.values(), key=lambda x: x.room_name.lower())
    
    def get_fuzzy_suggestions(self, query: str, limit: int = 5, threshold: int = 60) -> List[str]:
        """
        Get fuzzy match suggestions for a query.
        
        Args:
            query: Search query string
            limit: Maximum number of suggestions
            threshold: Minimum match score (0-100)
            
        Returns:
            List of room names as suggestions
        """
        if not query:
            return []
            
        fuzzy_matches = process.extract(
            query, 
            self.room_names, 
            limit=limit, 
            score_cutoff=threshold
        )
        
        return [match[0] for match in fuzzy_matches]


class RouteCalculator:
    """Handles route calculation between two geographical points."""
    
    @staticmethod
    def get_walking_route(from_lat: float, from_lon: float, 
                         to_lat: float, to_lon: float, 
                         timeout: int = 5) -> Optional[RouteInfo]:
        """
        Calculate walking route between two points using OSRM routing service.
        
        Args:
            from_lat: Starting latitude
            from_lon: Starting longitude  
            to_lat: Destination latitude
            to_lon: Destination longitude
            timeout: Request timeout in seconds
            
        Returns:
            RouteInfo object with distance, duration, and geometry, or None if failed
        """
        try:
            # OSRM API expects lon,lat format
            url = (f"http://router.project-osrm.org/route/v1/foot/"
                   f"{from_lon},{from_lat};{to_lon},{to_lat}?"
                   f"overview=full&geometries=geojson")
            
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            
            if not data or "routes" not in data or len(data["routes"]) == 0:
                return None
                
            route_data = data["routes"][0]
            
            return RouteInfo(
                distance_km=round(route_data["distance"] / 1000, 2),
                duration_minutes=round(route_data["duration"] / 60, 1),
                geometry=route_data["geometry"]
            )
            
        except (requests.exceptions.RequestException, KeyError, ValueError) as e:
            print(f"Route calculation failed: {e}")
            return None


class AccessController:
    """Handles access control based on GPS location and campus boundaries."""
    
    def __init__(self, campus_boundary: List[Tuple[float, float]]):
        """
        Initialize access controller with campus boundary.
        
        Args:
            campus_boundary: List of (lat, lon) tuples defining campus boundary
        """
        self.campus_boundary = campus_boundary
    
    def is_location_valid(self, location: Optional[UserLocation]) -> Tuple[bool, str]:
        """
        Check if user location is valid and within campus boundaries.
        
        Args:
            location: UserLocation object with GPS coordinates, or None
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if location is None:
            return False, "GPS is not available. This service is restricted to users physically within the MUT campus boundaries."
        
        if not self.campus_boundary:
            return False, "Campus boundary data is not available."
            
        is_inside = GeometryUtils.point_in_polygon(
            location.lat, 
            location.lon, 
            self.campus_boundary
        )
        
        if not is_inside:
            return False, "You are outside the MUT campus boundaries. This application is only accessible from within campus."
            
        return True, ""


# Configuration constants
class Config:
    """Configuration constants for the application."""
    
    # File paths
    ROOMS_FILE = "campus-room-finder/rooms.json"
    BOUNDARIES_FILE = "campus-room-finder/boundaries.csv"
    
    # Map settings
    DEFAULT_ZOOM = 17
    ROUTE_COLOR = "green"
    ROUTE_WEIGHT = 4
    CAMPUS_BOUNDARY_COLOR = "blue"
    CAMPUS_BOUNDARY_WEIGHT = 3
    CAMPUS_BOUNDARY_OPACITY = 0.05
    
    # Search settings
    FUZZY_MATCH_LIMIT = 5
    FUZZY_MATCH_THRESHOLD = 60
    
    # Route calculation
    ROUTE_TIMEOUT = 5
