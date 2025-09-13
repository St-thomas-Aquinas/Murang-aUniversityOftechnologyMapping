# Campus Room Finder - Setup and Requirements

## 📁 Project Structure

The codebase has been refactored into three main components with clear separation of concerns:

```
campus-room-finder/
├── campus_data_logic.py       # Core business logic and data models
├── campus_ui_components.py    # UI components and map visualization
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
├── rooms.json               # Room data file
└── boundaries.csv           # Campus boundary data
```

## 🏗️ Architecture Overview

### 1. **Business Logic Layer** (`campus_data_logic.py`)
- **Data Models**: `Room`, `UserLocation`, `RouteInfo` - Clean data structures
- **Utility Classes**: 
  - `GeometryUtils` - Spatial calculations and polygon operations
  - `DataLoader` - File loading and parsing with robust error handling
  - `RoomSearchEngine` - Search functionality with fuzzy matching
  - `RouteCalculator` - Route calculation using OSRM API
  - `AccessController` - GPS-based access control
- **Configuration**: Centralized constants and settings

### 2. **User Interface Layer** (`campus_ui_components.py`)
- **UI Components**: Reusable Streamlit components for consistent styling
- **Map Management**: 
  - `MapStyleManager` - Handle different tile layers and attributions
  - `MapRenderer` - Create and configure interactive maps
- **GPS Integration**: `GPSManager` - Handle browser geolocation API
- **Search Interface**: `SearchInterface` - Room search UI with suggestions
- **Main App**: `CampusRoomFinderApp` - Orchestrates all components

### 3. **Application Entry Point** (`main.py`)
- Simple entry point that imports and runs the main application

## 📦 Dependencies

```txt
streamlit>=1.28.0
folium>=0.14.0
streamlit-folium>=0.13.0
streamlit-js-eval>=0.1.0
requests>=2.31.0
rapidfuzz>=3.0.0
branca>=0.6.0
```

## 🚀 Installation and Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Prepare Data Files**:
   - Ensure `rooms.json` contains room data with required fields
   - Ensure `boundaries.csv` contains campus boundary coordinates

3. **Run Application**:
   ```bash
   streamlit run main.py
   ```

## 📋 Data File Formats

### rooms.json
```json
[
  {
    "room_name": "Room 101A",
    "building": "Main Building",
    "floor": "1",
    "lat": -0.1234567,
    "lon": 36.1234567
  }
]
```

### boundaries.csv
Supports multiple formats:

**Option 1: WKT Format**
```csv
WKT
"POINT(36.1234567 -0.1234567)"
"POINT(36.1234568 -0.1234568)"
```

**Option 2: Separate Columns**
```csv
lat,lon
-0.1234567,36.1234567
-0.1234568,36.1234568
```

## 🔧 Key Features

### ✅ **Clean Separation of Concerns**
- Business logic completely separated from UI
- Easy to test individual components
- Clear interfaces between layers

### ✅ **Robust Error Handling**
- Graceful handling of missing files
- Network request timeouts and retries
- Invalid coordinate data handling

### ✅ **Flexible Data Loading**
- Support for multiple coordinate formats
- WKT parsing with fallbacks
- Automatic data validation and cleaning

### ✅ **Advanced Search Capabilities**
- Combined substring and fuzzy matching
- Configurable search thresholds
- Interactive suggestion system

### ✅ **Professional Map Features**
- Multiple tile layer support
- Campus boundary enforcement
- Dynamic route calculation
- Responsive marker placement

### ✅ **Access Control**
- GPS-based location verification
- Campus boundary validation
- User-friendly error pages

## 🛠️ Customization

### Adding New Map Styles
Edit `MapStyleManager` in `campus_ui_components.py`:
```python
TILE_LAYERS = {
    "Custom Style": "https://your-tile-server/{z}/{x}/{y}.png"
}
```

### Modifying Search Behavior
Adjust constants in `Config` class in `campus_data_logic.py`:
```python
FUZZY_MATCH_THRESHOLD = 60  # Lower = more lenient matching
FUZZY_MATCH_LIMIT = 5       # Max suggestions to show
```

### Changing Access Control
Modify `AccessController` to implement different validation logic:
```python
def is_location_valid(self, location):
    # Implement custom validation logic
    return True, ""
```

## 🧪 Testing

The modular structure makes testing much easier:

```python
# Test business logic independently
from campus_data_logic import GeometryUtils, RoomSearchEngine

# Test point-in-polygon
assert GeometryUtils.point_in_polygon(0, 0, [(1,1), (-1,1), (-1,-1), (1,-1)])

# Test search functionality
rooms = [Room("Room A", "Building 1", "1", 0, 0)]
search_engine = RoomSearchEngine(rooms)
results = search_engine.search("Room")
```

## 📝 Code Quality Features

- **Type Hints**: Full type annotation for better IDE support and documentation
- **Docstrings**: Comprehensive documentation for all classes and methods  
- **Data Classes**: Clean, immutable data structures
- **Error Handling**: Comprehensive exception handling with user-friendly messages
- **Constants**: Centralized configuration management
- **Single Responsibility**: Each class has a clear, focused purpose

## 🔄 Migration from Original Code

The refactored code maintains 100% functional compatibility while providing:
- Better maintainability and readability
- Easier testing and debugging
- More professional code organization
- Enhanced error handling and robustness
- Clear extension points for new features
