import React, { useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix default icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom markers
const createCustomIcon = (color) => {
  return L.divIcon({
    className: 'custom-div-icon',
    html: `<div style="background-color: ${color}; width: 14px; height: 14px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.5);"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7]
  });
};

const originIcon = createCustomIcon('#3b82f6'); // blue
const destIcon = createCustomIcon('#ef4444'); // red
const transferIcon = createCustomIcon('#f59e0b'); // amber
const busIcon = createCustomIcon('#10b981'); // emerald green

const MapBounds = ({ allPositions }) => {
  const map = useMap();
  useEffect(() => {
    if (allPositions && allPositions.length > 0) {
      const bounds = L.latLngBounds(allPositions);
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [allPositions, map]);
  return null;
};

export default function TransitMap({ routeOptions = [], selectedRouteId, onRouteSelect, originCoords, destCoords, vehiclePositions = [] }) {
  
  // Flatten all geometries to bound the map
  const allPositions = useMemo(() => {
    let pos = [];
    routeOptions.forEach(r => {
      if (r.geometry && r.geometry.length > 0) {
        pos.push(...r.geometry);
      }
    });
    if (vehiclePositions && vehiclePositions.length > 0) {
      vehiclePositions.forEach(v => {
        if (v.latitude && v.longitude) pos.push([v.latitude, v.longitude]);
      });
    }
    pos.push([originCoords.lat, originCoords.lon]);
    pos.push([destCoords.lat, destCoords.lon]);
    return pos;
  }, [routeOptions, originCoords, destCoords, vehiclePositions]);

  const activeRoute = routeOptions.find(r => r.route_id === selectedRouteId);
  const activeHasGeometry = activeRoute?.geometry && activeRoute.geometry.length > 0;

  return (
    <div className="relative w-full h-[400px] sm:h-[550px] rounded-3xl overflow-hidden border border-[var(--border-color)] shadow-xl z-0">
      <MapContainer 
        center={[originCoords.lat, originCoords.lon]} 
        zoom={10} 
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Draw alternative routes first (underneath) */}
        {routeOptions.filter(r => r.route_id !== selectedRouteId).map(route => {
          const hasGeo = route.geometry && route.geometry.length > 0;
          const pos = hasGeo ? route.geometry : [[originCoords.lat, originCoords.lon], [destCoords.lat, destCoords.lon]];
          return (
            <Polyline 
              key={route.route_id}
              positions={pos} 
              eventHandlers={{
                click: () => onRouteSelect && onRouteSelect(route.route_id)
              }}
              pathOptions={{ 
                color: '#9ca3af', // gray
                weight: 4, 
                opacity: 0.5,
                dashArray: hasGeo ? undefined : '5, 10'
              }} 
            />
          );
        })}

        {/* Draw active route legs */}
        {activeRoute && activeRoute.legs && activeRoute.legs.length > 0 ? (
          activeRoute.legs.map((leg, idx) => {
            const legHasGeo = leg.geometry && leg.geometry.length > 0;
            const pos = legHasGeo
              ? leg.geometry
              : (leg.origin_coords?.lat && leg.dest_coords?.lat
                  ? [[leg.origin_coords.lat, leg.origin_coords.lon], [leg.dest_coords.lat, leg.dest_coords.lon]]
                  : []);
            if (!pos || pos.length === 0) return null;

            const isFirst = leg.type === 'FIRST_MILE';
            const isLast = leg.type === 'LAST_MILE';
            const color = isFirst ? '#2563eb' : isLast ? '#0891b2' : '#7c3aed';
            const isDashed = isFirst || isLast || leg.mode === 'WALK' || leg.mode === 'ROAD';

            return (
              <Polyline
                key={`active-leg-${idx}`}
                positions={pos}
                pathOptions={{
                  color: color,
                  weight: isFirst || isLast ? 5 : 6,
                  opacity: 0.9,
                  dashArray: isDashed ? '8, 8' : undefined
                }}
              />
            );
          })
        ) : activeRoute && (
          <Polyline 
            positions={activeHasGeometry ? activeRoute.geometry : [[originCoords.lat, originCoords.lon], [destCoords.lat, destCoords.lon]]} 
            pathOptions={{ 
              color: '#7c3aed', // purple
              weight: 6, 
              opacity: 1,
              dashArray: activeHasGeometry ? undefined : '10, 10'
            }} 
          />
        )}
        
        {/* Origin Marker */}
        <Marker position={[originCoords.lat, originCoords.lon]} icon={originIcon}>
          <Popup>Origin</Popup>
        </Marker>
        
        {/* Destination Marker */}
        <Marker position={[destCoords.lat, destCoords.lon]} icon={destIcon}>
          <Popup>Destination</Popup>
        </Marker>

        {/* Transfer/Boarding Markers for Active Route */}
        {activeRoute?.legs?.map((leg, idx) => {
          const lat = leg.origin_coords?.lat || leg.from_lat || leg.boarding_stop?.lat;
          const lon = leg.origin_coords?.lon || leg.from_lon || leg.boarding_stop?.lon;
          if (lat && lon && (Math.abs(lat - originCoords.lat) > 0.001 || Math.abs(lon - originCoords.lon) > 0.001)) {
            return (
              <Marker key={`leg-start-${idx}`} position={[lat, lon]} icon={transferIcon}>
                <Popup>{leg.from_stop || leg.from_name || 'Boarding/Transfer'}</Popup>
              </Marker>
            );
          }
          return null;
        })}
        
        {/* Live Vehicle Markers */}
        {vehiclePositions && vehiclePositions.map((veh, idx) => (
          <Marker 
            key={veh.vehicle_id || `bus-${idx}`} 
            position={[veh.latitude, veh.longitude]} 
            icon={busIcon}
          >
            <Popup>
              <div className="text-xs font-semibold p-1">
                <div className="text-emerald-600 font-bold flex items-center gap-1">
                  🚌 Live Bus {veh.route_name || veh.route_id || ''}
                </div>
                <div>Vehicle: {veh.vehicle_id}</div>
                {veh.next_stop && <div>Next Stop: {veh.next_stop}</div>}
                {veh.eta_minutes !== null && veh.eta_minutes !== undefined && <div>ETA: {veh.eta_minutes} mins</div>}
                <div className="text-[10px] text-gray-400 mt-1">Updated: {veh.timestamp ? new Date(veh.timestamp).toLocaleTimeString() : 'Just now'}</div>
              </div>
            </Popup>
          </Marker>
        ))}

        <MapBounds allPositions={allPositions} />
      </MapContainer>

      {!activeHasGeometry && activeRoute && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-white/95 dark:bg-black/90 px-4 py-2 rounded-xl shadow-lg border border-amber-500/50 z-[1000] text-xs font-bold text-amber-600 dark:text-amber-400 flex items-center gap-2">
          <span>⚠️ Schematic Route — Exact Geometry Unavailable</span>
        </div>
      )}
    </div>
  );
}
