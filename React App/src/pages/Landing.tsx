import React, { useState, useEffect, useMemo, useRef } from 'react';
import mutRooms from '../campus-room-finder/rooms.json';
import { JSX } from 'react/jsx-runtime';

// This is not a standard React practice. In a modern React app,
// you would import CSS files and load scripts in public/index.html.
// We'll keep this part for now to match the original structure,
// but it's important to note for best practices.
const head = document.getElementsByTagName('head')[0];

const leafletCss = document.createElement('link');
leafletCss.rel = 'stylesheet';
leafletCss.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
if (!head.querySelector(`link[href="${leafletCss.href}"]`)) {
  head.appendChild(leafletCss);
}

const leafletJs = document.createElement('script');
leafletJs.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
if (!head.querySelector(`script[src="${leafletJs.src}"]`)) {
  head.appendChild(leafletJs);
}

const tailwindScript = document.createElement('script');
tailwindScript.src = 'https://cdn.tailwindcss.com';
if (!head.querySelector(`script[src="${tailwindScript.src}"]`)) {
  head.appendChild(tailwindScript);
}

// --- Icon Components ---
const icons = {
  Search: (props: JSX.IntrinsicAttributes & React.SVGProps<SVGSVGElement>) => (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" />
    </svg>
  ),
  Navigation: (props: JSX.IntrinsicAttributes & React.SVGProps<SVGSVGElement>) => (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="3 11 22 2 13 21 11 13 3 11" />
    </svg>
  ),
  Clock: (props: JSX.IntrinsicAttributes & React.SVGProps<SVGSVGElement>) => (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" />
    </svg>
  ),
  Building2: (props: JSX.IntrinsicAttributes & React.SVGProps<SVGSVGElement>) => (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z" /><path d="M6 12h4m6 0h2m-6 4h2m-6 4h2m-2-8h2" />
    </svg>
  ),
  Menu: (props: JSX.IntrinsicAttributes & React.SVGProps<SVGSVGElement>) => (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="4" x2="20" y1="12" y2="12" /><line x1="4" x2="20" y1="6" y2="6" /><line x1="4" x2="20" y1="18" y2="18" />
    </svg>
  ),
  X: (props: JSX.IntrinsicAttributes & React.SVGProps<SVGSVGElement>) => (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 6L6 18M6 6L18 18" />
    </svg>
  ),
  Route: (props: JSX.IntrinsicAttributes & React.SVGProps<SVGSVGElement>) => (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 15h12a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2Z" /><path d="M6 10h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2Z" /><path d="M12 15V9" />
    </svg>
  ),
  ChevronLeft: (props: JSX.IntrinsicAttributes & React.SVGProps<SVGSVGElement>) => (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m15 18-6-6 6-6" />
    </svg>
  ),
  ChevronRight: (props: JSX.IntrinsicAttributes & React.SVGProps<SVGSVGElement>) => (
    <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m9 18 6-6-6-6" />
    </svg>
  ),
};

// --- Constants ---
const MUTTheme = {
  PRIMARY: "#DC2626", // Red-600
  SECONDARY: "#16A34A", // Green-600
};

const TILE_LAYERS = {
  "🗺️ Standard": "OpenStreetMap",
  "🏔️ Terrain": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
  "🌙 Light": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}{r}.png",
};

const categoryIcons = {
  academic: '🎓',
  administrative: '🏛️',
  facility: '🏢',
  service: '🔧',
};

// --- MapRenderer Component ---
const MapRenderer = ({ userLocation, selectedRoom, tileLayerUrl, route }) => {
  const mapRef = useRef(null);
  const userMarkerRef = useRef(null);
  const roomMarkerRef = useRef(null);
  const routeLayerRef = useRef(null);
  const [leafletReady, setLeafletReady] = useState(false);

  const mutCampusBounds = useMemo(() => {
    if (typeof window.L === 'undefined') return null;
    return window.L.latLngBounds([-0.7170, 37.1460], [-0.7150, 37.1500]);
  }, [leafletReady]);

  useEffect(() => {
    const checkLeaflet = () => {
      if (typeof window.L !== 'undefined') {
        setLeafletReady(true);
      } else {
        setTimeout(checkLeaflet, 100);
      }
    };
    checkLeaflet();
  }, []);

  useEffect(() => {
    if (!leafletReady || !mutCampusBounds) return;

    if (!mapRef.current) {
      mapRef.current = window.L.map('map', {
        center: [-0.716, 37.148],
        zoom: 17,
        minZoom: 15,
        maxZoom: 20,
        zoomControl: false,
        maxBounds: mutCampusBounds,
        maxBoundsViscosity: 1.0,
      });
    }

    const map = mapRef.current;
    map.eachLayer((layer) => {
      if (layer instanceof window.L.TileLayer) {
        map.removeLayer(layer);
      }
    });

    const tileUrl = tileLayerUrl === "OpenStreetMap" ? 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png' : tileLayerUrl;
    window.L.tileLayer(tileUrl, { attribution: '© OpenStreetMap contributors' }).addTo(map);

    mutRooms.forEach(room => {
      const roomIcon = window.L.divIcon({
        className: 'custom-div-icon',
        html: `<div class="bg-white rounded-full w-8 h-8 shadow-md border-2 border-gray-300 flex items-center justify-center text-sm font-bold text-gray-800">${room.room_name?.substring(0, 1) || '?'}</div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      });

      const marker = window.L.marker([room.lat, room.lon], { icon: roomIcon }).addTo(map);
      marker.bindTooltip(`${room.room_name}<br/><small class="text-gray-600">${room.building}</small>`, {
        direction: 'top',
        className: 'bg-white rounded-lg p-2 text-sm text-gray-800 shadow-lg border'
      });
    });
  }, [leafletReady, tileLayerUrl, mutCampusBounds]);

  useEffect(() => {
    if (!leafletReady || !mapRef.current) return;
    const map = mapRef.current;

    const userIcon = window.L.divIcon({
      className: 'custom-div-icon',
      html: `<div class="bg-blue-500 rounded-full w-4 h-4 shadow-lg ring-4 ring-blue-200 animate-pulse"></div>`,
      iconSize: [16, 16],
      iconAnchor: [8, 8]
    });

    if (userLocation) {
      if (userMarkerRef.current) {
        userMarkerRef.current.setLatLng([userLocation.lat, userLocation.lon]);
      } else {
        userMarkerRef.current = window.L.marker([userLocation.lat, userLocation.lon], { icon: userIcon }).addTo(map);
        userMarkerRef.current.bindTooltip("You are here", { direction: 'top', permanent: false, className: 'bg-blue-500 text-white rounded-lg p-2 text-xs shadow-lg' });
      }
    }

    if (roomMarkerRef.current) { map.removeLayer(roomMarkerRef.current); roomMarkerRef.current = null; }
    if (routeLayerRef.current) { map.removeLayer(routeLayerRef.current); routeLayerRef.current = null; }

    if (selectedRoom) {
      const roomIcon = window.L.divIcon({
        className: 'custom-div-icon',
        html: `<div class="bg-red-600 rounded-full w-8 h-8 shadow-lg ring-4 ring-red-200 animate-bounce flex items-center justify-center text-white text-base font-bold">📍</div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      });
      roomMarkerRef.current = window.L.marker([selectedRoom.lat, selectedRoom.lon], { icon: roomIcon }).addTo(map);

      if (route) {
        routeLayerRef.current = window.L.geoJSON(route.geometry, { style: { color: MUTTheme.SECONDARY, weight: 5, opacity: 0.9, dashArray: "10, 5" } }).addTo(map);
        map.fitBounds(routeLayerRef.current.getBounds(), { padding: [50, 50] });
      } else {
        map.panTo([selectedRoom.lat, selectedRoom.lon]);
      }
    }
  }, [leafletReady, userLocation, selectedRoom, route]);

  return (
    <div className="relative w-full h-full">
      <div id="map" className="w-full h-full"></div>
      <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm rounded-full px-3 py-1 text-xs font-medium text-gray-700 shadow-md">
        MUT Campus
      </div>
    </div>
  );
};

// --- ImageGallery Component ---
const ImageGallery = ({ images }) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  const goToNext = () => setCurrentIndex(prevIndex => (prevIndex + 1) % images.length);
  const goToPrev = () => setCurrentIndex(prevIndex => (prevIndex - 1 + images.length) % images.length);

  useEffect(() => {
    if (images.length > 1) {
      const timer = setInterval(goToNext, 5000);
      return () => clearInterval(timer);
    }
  }, [images.length]);

  return (
    <div className="relative w-full h-48 overflow-hidden rounded-2xl mb-4 shadow-inner">
      <div className="flex transition-transform duration-500 ease-in-out h-full" style={{ transform: `translateX(-${currentIndex * 100}%)` }}>
        {images.map((image, index) => (
          <div key={index} className="w-full flex-shrink-0">
            <img src={image} alt={`Location view ${index + 1}`} className="object-cover w-full h-full" />
          </div>
        ))}
      </div>
      {images.length > 1 && (
        <>
          <button onClick={goToPrev} className="absolute top-1/2 left-3 -translate-y-1/2 bg-white/60 p-2 rounded-full backdrop-blur-sm shadow-md transition-transform hover:scale-110"><icons.ChevronLeft className="w-5 h-5 text-gray-700" /></button>
          <button onClick={goToNext} className="absolute top-1/2 right-3 -translate-y-1/2 bg-white/60 p-2 rounded-full backdrop-blur-sm shadow-md transition-transform hover:scale-110"><icons.ChevronRight className="w-5 h-5 text-gray-700" /></button>
        </>
      )}
    </div>
  );
};

// --- Main Landing Component ---
const Landing = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [routeInfo, setRouteInfo] = useState(null);
  const [showSheet, setShowSheet] = useState(false);
  const [selectedMapStyle, setSelectedMapStyle] = useState("🗺️ Standard");
  const [filteredRooms, setFilteredRooms] = useState([]);

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => { setUserLocation({ lat: position.coords.latitude, lon: position.coords.longitude }); },
        (error) => {
          console.error("Error getting user location:", error);
          setUserLocation({ lat: -0.716 + (Math.random() - 0.5) * 0.003, lon: 37.148 + (Math.random() - 0.5) * 0.003 });
        }
      );
    } else {
      setUserLocation({ lat: -0.716 + (Math.random() - 0.5) * 0.003, lon: 37.148 + (Math.random() - 0.5) * 0.003 });
    }
  }, []);
  
  // Use a dedicated useEffect for filtering to prevent infinite loops
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredRooms([]);
      return;
    }
    const lowerCaseQuery = searchQuery.toLowerCase();
    const rooms = mutRooms.filter(room => (
      room.room_name?.toLowerCase().includes(lowerCaseQuery) ||
      room.building?.toLowerCase().includes(lowerCaseQuery) ||
      (room.floor && String(room.floor).toLowerCase().includes(lowerCaseQuery))
    ));
    setFilteredRooms(rooms);
  }, [searchQuery]);

  const handleShowDirections = () => {
    if (userLocation && selectedRoom) {
      const distance = Math.sqrt(Math.pow((userLocation.lat - selectedRoom.lat) * 111000, 2) + Math.pow((userLocation.lon - selectedRoom.lon) * 111000, 2)) / 1000;
      const duration = (distance / 5) * 60; // Assuming 5km/h walking speed
      setRouteInfo({
        distance_km: distance.toFixed(2),
        duration_minutes: Math.max(1, Math.round(duration)).toString(),
        geometry: { type: "LineString", coordinates: [[userLocation.lon, userLocation.lat], [selectedRoom.lon, selectedRoom.lat]] }
      });
    } else {
      alert("Please enable location services or select a room to get directions.");
    }
  };

  const handleRoomSelect = (room) => {
    setSelectedRoom(room);
    setSearchQuery(room.room_name);
    setShowSheet(true);
    setRouteInfo(null); // Clear previous route when a new room is selected
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setSelectedRoom(null);
    setShowSheet(false);
    setRouteInfo(null);
  };

  const categories = [
    { key: 'academic', name: 'Academic', icon: '🎓', color: 'bg-blue-50 text-blue-700 border-blue-200' },
    { key: 'facility', name: 'Facilities', icon: '🏢', color: 'bg-green-50 text-green-700 border-green-200' },
    { key: 'service', name: 'Services', icon: '🔧', color: 'bg-purple-50 text-purple-700 border-purple-200' },
    { key: 'administrative', name: 'Admin', icon: '🏛️', color: 'bg-orange-50 text-orange-700 border-orange-200' }
  ];

  const popularRooms = mutRooms.slice(0, 6);

  return (
    <div className="relative h-screen overflow-hidden bg-gray-50 flex flex-col md:flex-row">
      
      {/* --- Map Container --- */}
      <div className="flex-1 w-full h-full md:w-3/4">
        <MapRenderer
          userLocation={userLocation}
          selectedRoom={selectedRoom}
          tileLayerUrl={TILE_LAYERS[selectedMapStyle]}
          route={routeInfo}
        />
      </div>

      {/* --- Desktop Sidebar and Mobile Bottom Sheet --- */}
      <div className={`
        fixed inset-x-0 bottom-0 z-20
        md:static md:w-1/4 md:z-auto
        md:border-l md:border-gray-200
        bg-white
        shadow-xl md:shadow-none
        rounded-t-2xl md:rounded-none
        transition-transform duration-500 ease-in-out
        ${showSheet ? 'translate-y-0' : 'translate-y-full md:translate-y-0'}
        md:h-screen md:overflow-y-auto
      `}>
        {/* Mobile drag handle */}
        <div className="md:hidden w-12 h-1 bg-gray-300 rounded-full mx-auto my-3"></div>
        
        <div className="p-4 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-lg text-gray-800 hidden md:block">Campus Finder</h2>
            <button 
              onClick={handleClearSearch}
              className="md:hidden text-gray-500 hover:text-red-500 transition-colors"
            >
              <icons.X className="w-6 h-6" />
            </button>
          </div>

          {!selectedRoom ? (
            <div className="space-y-4">
              <div className="relative">
                <icons.Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  placeholder="Search rooms, labs, offices..."
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:border-red-500 focus:outline-none text-sm bg-white shadow-sm"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>

              {searchQuery === "" && (
                <>
                  <div className="grid grid-cols-2 gap-2">
                    {categories.map(category => (
                      <button
                        key={category.key}
                        className={`p-3 rounded-xl border text-sm font-medium transition-all ${category.color}`}
                      >
                        <span className="mr-2">{category.icon}</span>
                        {category.name}
                      </button>
                    ))}
                  </div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-2">Popular Locations</h3>
                  <div className="grid grid-cols-2 gap-2">
                    {popularRooms.map(room => (
                      <button
                        key={room.room_id}
                        onClick={() => handleRoomSelect(room)}
                        className="p-2 bg-white rounded-lg border border-gray-200 text-left hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-sm">{categoryIcons[room.category]}</span>
                          <span className="text-xs font-medium text-gray-800 truncate">{room.room_name}</span>
                        </div>
                      </button>
                    ))}
                  </div>
                </>
              )}

              {filteredRooms.length > 0 && (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {filteredRooms.map(room => (
                    <button
                      key={room.room_id}
                      onClick={() => handleRoomSelect(room)}
                      className={`w-full text-left p-3 rounded-xl transition-all ${
                        selectedRoom?.room_id === room.room_id
                          ? 'bg-red-50 border border-red-200'
                          : 'bg-white border border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-lg">{categoryIcons[room.category]}</span>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 text-sm truncate">{room.room_name}</p>
                          <p className="text-xs text-gray-500 truncate">{room.building} • {room.floor}</p>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">
              {selectedRoom.images && selectedRoom.images.length > 0 && <ImageGallery images={selectedRoom.images} />}
              <div className="flex items-start gap-3 mb-3">
                <span className="text-2xl">{categoryIcons[selectedRoom.category]}</span>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900">{selectedRoom.room_name}</h3>
                  <p className="text-sm text-gray-500">{selectedRoom.building}</p>
                  <p className="text-xs text-gray-400">{selectedRoom.floor}</p>
                </div>
              </div>
              
              <button
                onClick={handleShowDirections}
                className="w-full bg-red-600 text-white py-3 rounded-xl font-medium flex items-center justify-center gap-2 hover:bg-red-700 transition-colors mb-4"
              >
                <icons.Navigation className="w-5 h-5" />
                Show Directions
              </button>

              {routeInfo && (
                <div className="flex gap-4 mb-4">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <icons.Route className="w-4 h-4 text-green-600" />
                    <span>{routeInfo.distance_km} km</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <icons.Clock className="w-4 h-4 text-green-600" />
                    <span>{routeInfo.duration_minutes} min walk</span>
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="pt-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Map Style</h3>
            <div className="grid grid-cols-2 gap-2">
              {Object.keys(TILE_LAYERS).map(style => (
                <button
                  key={style}
                  onClick={() => setSelectedMapStyle(style)}
                  className={`p-3 rounded-xl border text-sm font-medium transition-all ${
                    selectedMapStyle === style
                      ? 'bg-red-50 text-red-700 border-red-200'
                      : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  {style}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {!showSheet && (
        <button
          onClick={() => setShowSheet(true)}
          className="fixed bottom-6 right-6 md:hidden bg-red-600 text-white w-14 h-14 rounded-full shadow-lg flex items-center justify-center hover:bg-red-700 transition-colors z-30"
        >
          <icons.Search className="w-6 h-6" />
        </button>
      )}
    </div>
  );
};

export default Landing;