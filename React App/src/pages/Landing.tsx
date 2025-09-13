import React, { useState, useEffect, useMemo, useRef } from 'react';

import mutRooms from '../campus-room-finder/rooms.json';

// Declare global type for Leaflet loaded via CDN

declare global {

interface Window {

L: any;

}

}



// Load Leaflet CSS and JS

const head = document.getElementsByTagName('head')[0];

const leafletCss = document.createElement('link');

leafletCss.rel = 'stylesheet';

leafletCss.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';

head.appendChild(leafletCss);



const leafletJs = document.createElement('script');

leafletJs.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';

head.appendChild(leafletJs);



// Tailwind CSS CDN

const tailwindScript = document.createElement('script');

tailwindScript.src = 'https://cdn.tailwindcss.com';

head.appendChild(tailwindScript);



// Icon components

const icons = {

Search: (props: any) => (

<svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">

<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>

</svg>

),

MapPin: (props: any) => (

<svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">

<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>

</svg>

),

Navigation: (props: any) => (

<svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">

<polygon points="3 11 22 2 13 21 11 13 3 11"/>

</svg>

),

Clock: (props: any) => (

<svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">

<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>

</svg>

),

Building2: (props: any) => (

<svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">

<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z"/><path d="M6 12h4m6 0h2m-6 4h2m-6 4h2m-2-8h2"/>

</svg>

),

Menu: (props: any) => (

<svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">

<line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/>

</svg>

),

X: (props: any) => (

<svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">

<path d="m18 6-12 12"/><path d="m6 6 12 12"/>

</svg>

),

Route: (props: any) => (

<svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">

<path d="M6 15h12a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2Z"/><path d="M6 10h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v4a2 2 0 0 0 2 2Z"/><path d="M12 15V9"/>

</svg>

)

};



// MUT Theme Colors - Enhanced for mobile

const MUTTheme = {

PRIMARY: "#DC2626", // Red-600

PRIMARY_DARK: "#B91C1C", // Red-700

SECONDARY: "#16A34A", // Green-600

ACCENT: "#2563EB", // Blue-600

BACKGROUND: "#F8FAFC", // Slate-50

SURFACE: "#FFFFFF",

TEXT_PRIMARY: "#0F172A", // Slate-900

TEXT_SECONDARY: "#64748B", // Slate-500

BORDER: "#E2E8F0" // Slate-200

};



interface Room {

room_name: string;

building: string;

floor: string;

lat: number;

lon: number;

// category: 'academic' | 'administrative' | 'facility' | 'service';

}



interface UserLocation {

lat: number;

lon: number;

}



interface RouteInfo {

distance_km: string;

duration_minutes: string;

geometry: {

type: "LineString";

coordinates: [number, number][];

};

}







// MUT Campus boundary (approximate)

const mutCampusBoundary = [

[-0.6200, 37.1470],

[-0.6200, 37.1530],

[-0.6140, 37.1530],

[-0.6140, 37.1470],

[-0.6200, 37.1470]

];



const categoryIcons = {

academic: '🎓',

administrative: '🏛️',

facility: '🏢',

service: '🔧'

};



const MapRenderer: React.FC<{

userLocation: UserLocation;

selectedRoom: Room | null;

route: RouteInfo | null;

}> = ({ userLocation, selectedRoom, route }) => {

const mapRef = useRef<any>(null);

const userMarkerRef = useRef<any>(null);

const roomMarkerRef = useRef<any>(null);

const routeLayerRef = useRef<any>(null);

const campusBoundaryRef = useRef<any>(null);

const [leafletReady, setLeafletReady] = useState(false);



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

if (!leafletReady || mapRef.current) return;



// Center on MUT campus

const mutCenter: [number, number] = [-0.6170, 37.1500];


const map = window.L.map('map', {

center: mutCenter,

zoom: 17,

minZoom: 15,

maxZoom: 20,

zoomControl: false,

});


mapRef.current = map;



// Add tile layer

window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {

attribution: '© OpenStreetMap contributors',

}).addTo(map);



// Add campus boundary

campusBoundaryRef.current = window.L.polygon(mutCampusBoundary, {

color: MUTTheme.PRIMARY,

weight: 3,

fillColor: MUTTheme.SECONDARY,

fillOpacity: 0.1

}).addTo(map);



// Add all room markers

mutRooms.forEach(room => {

// const icon = categoryIcons[room.category];

const roomIcon = window.L.divIcon({

className: 'custom-div-icon',

html: `<div class="bg-white rounded-full w-8 h-8 shadow-lg border-2 border-gray-300 flex items-center justify-center text-sm">${name}</div>`,

iconSize: [32, 32],

iconAnchor: [16, 16]

});


const marker = window.L.marker([room.lat, room.lon], { icon: roomIcon }).addTo(map);

marker.bindTooltip(`${room.room_name}<br/><small class="text-gray-600">${room.building}</small>`, {

direction: 'top',

className: 'bg-white rounded-lg p-2 text-sm text-gray-800 shadow-lg border'

});

});



return () => {

if (mapRef.current) {

mapRef.current.remove();

mapRef.current = null;

}

};

}, [leafletReady]);



useEffect(() => {

if (!leafletReady || !mapRef.current) return;



const map = mapRef.current;



// Update user marker

const userIcon = window.L.divIcon({

className: 'custom-div-icon',

html: `<div class="bg-blue-500 rounded-full w-4 h-4 shadow-lg ring-4 ring-blue-200 animate-pulse"></div>`,

iconSize: [16, 16],

iconAnchor: [8, 8]

});



if (userMarkerRef.current) {

userMarkerRef.current.setLatLng([userLocation.lat, userLocation.lon]);

} else {

userMarkerRef.current = window.L.marker([userLocation.lat, userLocation.lon], { icon: userIcon }).addTo(map);

userMarkerRef.current.bindTooltip("You are here", {

direction: 'top',

permanent: false,

className: 'bg-blue-500 text-white rounded-lg p-2 text-xs shadow-lg'

});

}



// Update selected room marker and route

if (roomMarkerRef.current) {

map.removeLayer(roomMarkerRef.current);

roomMarkerRef.current = null;

}

if (routeLayerRef.current) {

map.removeLayer(routeLayerRef.current);

routeLayerRef.current = null;

}



if (selectedRoom) {

const roomIcon = window.L.divIcon({

className: 'custom-div-icon',

html: `<div class="bg-red-500 rounded-full w-6 h-6 shadow-lg ring-4 ring-red-200 animate-bounce flex items-center justify-center text-white text-xs font-bold">📍</div>`,

iconSize: [24, 24],

iconAnchor: [12, 12]

});


roomMarkerRef.current = window.L.marker([selectedRoom.lat, selectedRoom.lon], { icon: roomIcon }).addTo(map);


if (route) {

routeLayerRef.current = window.L.geoJSON(route.geometry as any, {

style: {

color: MUTTheme.SECONDARY,

weight: 4,

opacity: 0.8,

dashArray: "10, 5"

}

}).addTo(map);


// Fit bounds to show both user and destination

const bounds = window.L.latLngBounds([

[userLocation.lat, userLocation.lon],

[selectedRoom.lat, selectedRoom.lon]

]);

map.fitBounds(bounds, { padding: [20, 20] });

}

}



}, [leafletReady, userLocation, selectedRoom, route]);



return (

<div className="relative">

<div id="map" className="w-full h-64 sm:h-80 md:h-96 rounded-xl shadow-lg"></div>

<div className="absolute top-3 right-3 bg-white/90 backdrop-blur-sm rounded-lg px-2 py-1 text-xs text-gray-600 shadow">

MUT Campus

</div>

</div>

);

};



const MobileHeader: React.FC<{ onMenuToggle: () => void; showMenu: boolean }> = ({ onMenuToggle, showMenu }) => (

<div className="bg-gradient-to-r from-red-600 to-red-700 text-white sticky top-0 z-50 shadow-lg">

<div className="px-4 py-3 flex items-center justify-between">

<div className="flex items-center gap-3">

<div className="bg-white text-red-600 font-black text-sm px-2 py-1 rounded-lg">

MUT

</div>

<div>

<h1 className="text-lg font-bold">Campus Finder</h1>

<p className="text-xs text-red-100">Find your way around</p>

</div>

</div>

<button

onClick={onMenuToggle}

className="p-2 rounded-lg bg-white/10 backdrop-blur-sm"

>

{showMenu ? <icons.X className="w-5 h-5" /> : <icons.Menu className="w-5 h-5" />}

</button>

</div>

</div>

);



const SearchSection: React.FC<{

searchQuery: string;

onSearchChange: (e: React.ChangeEvent<HTMLInputElement>) => void;

filteredRooms: Room[];

onRoomSelect: (room: Room) => void;

selectedRoom: Room | null;

}> = ({ searchQuery, onSearchChange, filteredRooms, onRoomSelect, selectedRoom }) => {

const categories = [

{ key: 'academic', name: 'Academic', icon: '🎓', color: 'bg-blue-50 text-blue-700 border-blue-200' },

{ key: 'facility', name: 'Facilities', icon: '🏢', color: 'bg-green-50 text-green-700 border-green-200' },

{ key: 'service', name: 'Services', icon: '🔧', color: 'bg-purple-50 text-purple-700 border-purple-200' },

{ key: 'administrative', name: 'Admin', icon: '🏛️', color: 'bg-orange-50 text-orange-700 border-orange-200' }

];



const popularRooms = mutRooms.slice(0, 6);



return (

<div className="space-y-4">

{/* Search Input */}

<div className="relative">

<icons.Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />

<input

type="text"

placeholder="Search rooms, labs, offices..."

className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 focus:border-red-500 focus:outline-none text-sm bg-white shadow-sm"

value={searchQuery}

onChange={onSearchChange}

/>

</div>



{/* Category Pills */}

{searchQuery === "" && (

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

)}



{/* Search Results */}

{filteredRooms.length > 0 && (

<div className="space-y-2 max-h-64 overflow-y-auto">

{filteredRooms.map(room => (

<button

key={`${room.room_name}-${room.building}`}

onClick={() => onRoomSelect({ ...room, floor: String(room.floor), building: room.building ?? "" })}

className={`w-full text-left p-3 rounded-xl transition-all ${

selectedRoom?.room_name === room.room_name

? 'bg-red-50 border border-red-200'

: 'bg-white border border-gray-200 hover:bg-gray-50'

}`}

>

<div className="flex items-start gap-3">

{/* <span className="text-lg">{categoryIcons[room.category]}</span> */}

<div className="flex-1 min-w-0">

<p className="font-medium text-gray-900 text-sm truncate">{room.room_name}</p>

<p className="text-xs text-gray-500 truncate">{room.building} • {room.floor}</p>

</div>

</div>

</button>

))}

</div>

)}



{/* Popular Locations */}

{searchQuery === "" && (

<div>

<h3 className="text-sm font-semibold text-gray-700 mb-2">Popular Locations</h3>

<div className="grid grid-cols-2 gap-2">

{popularRooms.map(room => (

<button

key={room.room_name}

onClick={() => onRoomSelect({ ...room, floor: String(room.floor), building: room.building ?? "" })}

className="p-2 bg-white rounded-lg border border-gray-200 text-left hover:bg-gray-50 transition-colors"

>

<div className="flex items-center gap-2">

{/* <span className="text-sm">{categoryIcons[room.category]}</span> */}

<span className="text-xs font-medium text-gray-800 truncate">{room.room_name}</span>

</div>

</button>

))}

</div>

</div>

)}

</div>

);

};



const RoomDetailsCard: React.FC<{ room: Room; route: RouteInfo | null; onStartNavigation: () => void }> = ({

room,

route,

onStartNavigation

}) => (

<div className="bg-white rounded-xl p-4 shadow-sm border border-gray-200">

<div className="flex items-start gap-3 mb-3">

{/* <span className="text-2xl">{categoryIcons[room.category]}</span> */}

<div className="flex-1 min-w-0">

<h3 className="font-semibold text-gray-900">{room.room_name}</h3>

<p className="text-sm text-gray-500">{room.building}</p>

<p className="text-xs text-gray-400">{room.floor}</p>

</div>

</div>



{route && (

<div className="flex gap-4 mb-4">

<div className="flex items-center gap-2 text-sm text-gray-600">

<icons.Route className="w-4 h-4" />

<span>{route.distance_km}km</span>

</div>

<div className="flex items-center gap-2 text-sm text-gray-600">

<icons.Clock className="w-4 h-4" />

<span>{route.duration_minutes}min walk</span>

</div>

</div>

)}



<button

onClick={onStartNavigation}

className="w-full bg-red-600 text-white py-3 rounded-xl font-medium flex items-center justify-center gap-2 hover:bg-red-700 transition-colors"

>

<icons.Navigation className="w-4 h-4" />

Get Directions

</button>

</div>

);



const StatusAlert: React.FC<{ message: string; type: 'success' | 'info' | 'error' | 'loading' }> = ({ message, type }) => {

const styles = {

success: 'bg-green-50 text-green-700 border-green-200',

info: 'bg-blue-50 text-blue-700 border-blue-200',

error: 'bg-red-50 text-red-700 border-red-200',

loading: 'bg-orange-50 text-orange-700 border-orange-200'

};



return (

<div className={`p-3 rounded-xl border text-sm ${styles[type]}`}>

<div className="flex items-center gap-2">

{type === 'loading' && <div className="animate-spin rounded-full h-4 w-4 border-2 border-current border-t-transparent"></div>}

<span>{message}</span>

</div>

</div>

);

};



const MUTCampusFinder: React.FC = () => {

const [searchQuery, setSearchQuery] = useState('');

const [selectedRoom, setSelectedRoom] = useState<Room | null>(null);

const [userLocation, setUserLocation] = useState<UserLocation | null>(null);

const [routeInfo, setRouteInfo] = useState<RouteInfo | null>(null);

const [showMenu, setShowMenu] = useState(false);

const [status, setStatus] = useState<{ message: string; type: 'success' | 'info' | 'error' | 'loading' } | null>(null);



// Get user location on load

useEffect(() => {

setStatus({ message: "Getting your location...", type: "loading" });


// Mock location within MUT campus

setTimeout(() => {

const mockUserLocation: UserLocation = {

lat: -0.6165 + (Math.random() - 0.5) * 0.003, // Random position within campus

lon: 37.1495 + (Math.random() - 0.5) * 0.003

};

setUserLocation(mockUserLocation);

setStatus({ message: "Location found successfully!", type: "success" });


setTimeout(() => setStatus(null), 2000);

}, 1500);

}, []);



// Calculate route when room is selected

useEffect(() => {

if (userLocation && selectedRoom) {

const distance = Math.sqrt(

Math.pow((userLocation.lat - selectedRoom.lat) * 111000, 2) +

Math.pow((userLocation.lon - selectedRoom.lon) * 111000, 2)

) / 1000; // Convert to km


const walkingSpeed = 5; // km/h

const duration = (distance / walkingSpeed) * 60; // minutes



setRouteInfo({

distance_km: distance.toFixed(2),

duration_minutes: Math.max(1, Math.round(duration)).toString(),

geometry: {

type: "LineString",

coordinates: [

[userLocation.lon, userLocation.lat],

[selectedRoom.lon, selectedRoom.lat]

]

}

});

} else {

setRouteInfo(null);

}

}, [userLocation, selectedRoom]);



const filteredRooms = useMemo(() => {

if (!searchQuery.trim()) return [];


return mutRooms

.filter(room =>

room.room_name.toLowerCase().includes(searchQuery.toLowerCase()) ||

(room.building ?? "").toLowerCase().includes(searchQuery.toLowerCase()) ||

String(room.floor).toLowerCase().includes(searchQuery.toLowerCase())

)

.map(room => ({

...room,

floor: String(room.floor),

building: room.building ?? ""

}));

}, [searchQuery]);



const handleRoomSelect = (room: Room) => {

setSelectedRoom(room);

setSearchQuery(room.room_name);

setShowMenu(false);

};



const handleStartNavigation = () => {

if (selectedRoom) {

setStatus({ message: `Navigation started to ${selectedRoom.room_name}`, type: "success" });

setTimeout(() => setStatus(null), 3000);

}

};



return (

<div className="min-h-screen bg-gray-50">

<MobileHeader onMenuToggle={() => setShowMenu(!showMenu)} showMenu={showMenu} />


<div className="relative">

{/* Main Content */}

<div className="p-4 space-y-4">

{/* Status Messages */}

{status && <StatusAlert message={status.message} type={status.type} />}


{/* Map */}

<div className="bg-white rounded-xl p-3 shadow-sm">

<MapRenderer

userLocation={userLocation || { lat: -0.6170, lon: 37.1500 }}

selectedRoom={selectedRoom}

route={routeInfo}

/>

</div>



{/* Selected Room Details */}

{selectedRoom && routeInfo && (

<RoomDetailsCard

room={selectedRoom}

route={routeInfo}

onStartNavigation={handleStartNavigation}

/>

)}



{/* Welcome Message */}

{!selectedRoom && (

<div className="text-center py-8 px-4">

<div className="text-4xl mb-3">🎓</div>

<h2 className="text-lg font-semibold text-gray-800 mb-2">Welcome to MUT Campus</h2>

<p className="text-sm text-gray-500">Tap the menu to search for any room, lab, or facility on campus</p>

</div>

)}

</div>



{/* Sliding Search Menu */}

<div className={`fixed inset-0 z-40 transition-all duration-300 ${showMenu ? 'visible' : 'invisible'}`}>

{/* Backdrop */}

<div

className={`absolute inset-0 bg-black/20 backdrop-blur-sm transition-opacity ${showMenu ? 'opacity-100' : 'opacity-0'}`}

onClick={() => setShowMenu(false)}

/>


{/* Menu Panel */}

<div className={`absolute top-0 left-0 w-full h-full bg-gray-50 transform transition-transform ${showMenu ? 'translate-x-0' : '-translate-x-full'}`}>

<div className="pt-16 p-4 h-full overflow-y-auto">

<SearchSection

searchQuery={searchQuery}

onSearchChange={(e) => setSearchQuery(e.target.value)}

filteredRooms={filteredRooms}

onRoomSelect={handleRoomSelect}

selectedRoom={selectedRoom}

/>

</div>

</div>

</div>



{/* Floating Action Button */}

{!showMenu && (

<button

onClick={() => setShowMenu(true)}

className="fixed bottom-6 right-6 bg-red-600 text-white w-14 h-14 rounded-full shadow-lg flex items-center justify-center hover:bg-red-700 transition-colors z-30"

>

<icons.Search className="w-6 h-6" />

</button>

)}



{/* Quick Access Bottom Sheet */}

{!showMenu && !selectedRoom && (

<div className="fixed bottom-0 left-0 right-0 bg-white rounded-t-2xl shadow-xl border-t border-gray-200 p-4 z-20">

<div className="w-12 h-1 bg-gray-300 rounded-full mx-auto mb-4"></div>

<h3 className="font-semibold text-gray-800 mb-3">Quick Access</h3>

<div className="grid grid-cols-3 gap-3">

{mutRooms.slice(0, 6).map(room => (

<button

key={room.room_name}

onClick={() => handleRoomSelect({ ...room, floor: String(room.floor), building: room.building ?? "" })}

className="p-3 bg-gray-50 rounded-xl text-center hover:bg-gray-100 transition-colors"

>

{/* <div className="text-lg mb-1">{categoryIcons[room.category]}</div> */}

<div className="text-xs font-medium text-gray-700 leading-tight">{room.room_name}</div>

</button>

))}

</div>

</div>

)}

</div>



{/* Footer */}

<div className="bg-gray-800 text-white text-center py-6 mt-16">

<div className="px-4">

<div className="text-sm font-semibold">

🚀 MUT Tech Club

</div>

<p className="text-xs opacity-75 mt-1">Innovating campus navigation</p>

</div>

</div>

</div>

);

};



export default MUTCampusFinder; 