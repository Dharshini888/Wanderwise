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
const stationIcon = L.divIcon({
  className: 'custom-station-icon',
  html: `<div style="background-color: #8b5cf6; width: 10px; height: 10px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 3px rgba(0,0,0,0.5);"></div>`,
  iconSize: [10, 10],
  iconAnchor: [5, 5]
});

// Coordinate validation and normalization
export const isValidCoord = (c) => {
  if (!c) return false;
  let lat, lon;
  if (Array.isArray(c) && c.length >= 2) {
    lat = Number(c[0]);
    lon = Number(c[1]);
  } else if (typeof c === 'object') {
    lat = Number(c.lat !== undefined ? c.lat : c.latitude);
    lon = Number(c.lon !== undefined ? c.lon : (c.lng !== undefined ? c.lng : c.longitude));
  }
  return typeof lat === 'number' && !isNaN(lat) && lat >= -90.0 && lat <= 90.0 &&
         typeof lon === 'number' && !isNaN(lon) && lon >= -180.0 && lon <= 180.0;
};

export const extractCoord = (c) => {
  if (!c) return null;
  let lat, lon;
  if (Array.isArray(c) && c.length >= 2) {
    lat = Number(c[0]);
    lon = Number(c[1]);
  } else if (typeof c === 'object') {
    lat = Number(c.lat !== undefined ? c.lat : c.latitude);
    lon = Number(c.lon !== undefined ? c.lon : (c.lng !== undefined ? c.lng : c.longitude));
  }
  if (typeof lat === 'number' && !isNaN(lat) && lat >= -90.0 && lat <= 90.0 &&
      typeof lon === 'number' && !isNaN(lon) && lon >= -180.0 && lon <= 180.0) {
    return [lat, lon];
  }
  return null;
};

const MapBounds = ({ allPositions }) => {
  const map = useMap();
  useEffect(() => {
    if (allPositions && allPositions.length > 0) {
      try {
        const bounds = L.latLngBounds(allPositions);
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
        }
      } catch (err) {
        console.warn('[TransitMap] Bounds fitting error:', err);
      }
    }
  }, [allPositions, map]);
  return null;
};

export default function TransitMap({ 
  routeOptions = [], 
  selectedRouteId, 
  onRouteSelect, 
  originCoords, 
  destCoords, 
  vehiclePositions = [] 
}) {
  const validOrigin = extractCoord(originCoords);
  const validDest = extractCoord(destCoords);

  // Flatten all geometries and markers safely to bound the map
  const allPositions = useMemo(() => {
    const pos = [];
    (routeOptions || []).forEach(r => {
      if (r && Array.isArray(r.geometry)) {
        r.geometry.forEach(pt => {
          const c = extractCoord(pt);
          if (c) pos.push(c);
        });
      }
      if (r && Array.isArray(r.intermediate_stops)) {
        r.intermediate_stops.forEach(st => {
          const c = extractCoord({ lat: st.lat, lon: st.lon || st.lng });
          if (c) pos.push(c);
        });
      }
      if (r && Array.isArray(r.legs)) {
        r.legs.forEach(leg => {
          if (Array.isArray(leg.geometry)) {
            leg.geometry.forEach(pt => {
              const c = extractCoord(pt);
              if (c) pos.push(c);
            });
          }
          const c1 = extractCoord(leg.origin_coords || { lat: leg.from_lat, lon: leg.from_lon });
          if (c1) pos.push(c1);
          const c2 = extractCoord(leg.dest_coords || { lat: leg.to_lat, lon: leg.to_lon });
          if (c2) pos.push(c2);
        });
      }
    });

    if (Array.isArray(vehiclePositions)) {
      vehiclePositions.forEach(v => {
        const c = extractCoord(v);
        if (c) pos.push(c);
      });
    }

    if (validOrigin) pos.push(validOrigin);
    if (validDest) pos.push(validDest);

    return pos;
  }, [routeOptions, validOrigin, validDest, vehiclePositions]);

  const activeRoute = (routeOptions || []).find(r => (r.route_id || r.journey_id) === selectedRouteId);
  const activeHasGeometry = activeRoute?.geometry && activeRoute.geometry.length > 2;
  const isSchematic = Boolean(!validOrigin || !validDest || (activeRoute && (!activeHasGeometry || (activeRoute.geometry?.length <= 2 && activeRoute.provider !== 'OSRM'))));

  // Safe fallback map center (validOrigin -> validDest -> first found position -> default)
  const defaultCenter = validOrigin || validDest || (allPositions.length > 0 ? allPositions[0] : [11.0168, 76.9558]);

  return (
    <div className="relative w-full h-[400px] sm:h-[550px] rounded-3xl overflow-hidden border border-[var(--border-color)] shadow-xl z-0">
      <MapContainer 
        center={defaultCenter} 
        zoom={validOrigin ? 10 : 6} 
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Draw alternative routes first (underneath) */}
        {(routeOptions || []).filter(r => r.route_id !== selectedRouteId).map(route => {
          const geoCoords = (route.geometry || []).map(extractCoord).filter(Boolean);
          const hasGeo = geoCoords.length > 0;
          const pos = hasGeo ? geoCoords : (validOrigin && validDest ? [validOrigin, validDest] : []);
          if (pos.length === 0) return null;

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
            const geoCoords = (leg.geometry || []).map(extractCoord).filter(Boolean);
            const legHasGeo = geoCoords.length > 0;
            const legFrom = extractCoord(leg.origin_coords || { lat: leg.from_lat, lon: leg.from_lon });
            const legTo = extractCoord(leg.dest_coords || { lat: leg.to_lat, lon: leg.to_lon });
            const pos = legHasGeo ? geoCoords : (legFrom && legTo ? [legFrom, legTo] : []);
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
          (() => {
            const geoCoords = (activeRoute.geometry || []).map(extractCoord).filter(Boolean);
            const pos = activeHasGeometry && geoCoords.length > 0
              ? geoCoords
              : (validOrigin && validDest ? [validOrigin, validDest] : []);
            if (pos.length === 0) return null;

            return (
              <Polyline 
                positions={pos} 
                pathOptions={{ 
                  color: '#7c3aed', // purple
                  weight: 6, 
                  opacity: 1,
                  dashArray: activeHasGeometry ? undefined : '10, 10'
                }} 
              />
            );
          })()
        )}
        
        {/* Origin Marker */}
        {validOrigin && (
          <Marker position={validOrigin} icon={originIcon}>
            <Popup>Origin</Popup>
          </Marker>
        )}
        
        {/* Destination Marker */}
        {validDest && (
          <Marker position={validDest} icon={destIcon}>
            <Popup>Destination</Popup>
          </Marker>
        )}

        {/* Transfer/Boarding Markers for Active Route */}
        {activeRoute?.legs?.map((leg, idx) => {
          const coord = extractCoord(
            leg.origin_coords || { lat: leg.from_lat || leg.boarding_stop?.lat, lon: leg.from_lon || leg.boarding_stop?.lon }
          );
          if (coord && validOrigin) {
            if (Math.abs(coord[0] - validOrigin[0]) > 0.001 || Math.abs(coord[1] - validOrigin[1]) > 0.001) {
              return (
                <Marker key={`leg-start-${idx}`} position={coord} icon={transferIcon}>
                  <Popup>{leg.from_stop || leg.from_name || 'Boarding/Transfer'}</Popup>
                </Marker>
              );
            }
          }
          return null;
        })}
        
        {/* Live Vehicle Markers */}
        {Array.isArray(vehiclePositions) && vehiclePositions.map((veh, idx) => {
          const coord = extractCoord(veh);
          if (!coord) return null;

          return (
            <Marker 
              key={veh.vehicle_id || `bus-${idx}`} 
              position={coord} 
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
          );
        })}

        {/* Intermediate Station Markers for Selected Train Route */}
        {activeRoute?.intermediate_stops?.map((stop, sIdx) => {
          const coord = extractCoord({ lat: stop.lat, lon: stop.lon || stop.lng });
          if (!coord) return null;
          return (
            <Marker key={`stop-${sIdx}`} position={coord} icon={stationIcon}>
              <Popup>
                <div className="text-xs font-semibold p-1">
                  <div className="text-purple-600 font-bold flex items-center gap-1">
                    🚆 {stop.station_name || stop.name} ({stop.station_code || stop.code || ''})
                  </div>
                  {stop.arrival && <div>Arr: {stop.arrival}</div>}
                  {stop.departure && <div>Dep: {stop.departure}</div>}
                  {stop.platform && <div>Platform: {stop.platform}</div>}
                  {stop.halt_minutes != null && Number(stop.halt_minutes) > 0 && (
                    <div className="text-gray-500 text-[10px]">Halt: {stop.halt_minutes} min</div>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}

        <MapBounds allPositions={allPositions} />
      </MapContainer>

      {isSchematic && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-white/95 dark:bg-black/90 px-4 py-2 rounded-xl shadow-lg border border-amber-500/50 z-[1000] text-xs font-bold text-amber-600 dark:text-amber-400 flex items-center gap-2">
          <span>⚠️ Schematic Route — {!validOrigin || !validDest ? 'Location Coordinates Unavailable' : 'Exact Geometry Unavailable'}</span>
        </div>
      )}
    </div>
  );
}
