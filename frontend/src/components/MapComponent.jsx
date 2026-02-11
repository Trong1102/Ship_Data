import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, CircleMarker } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useEffect, useRef } from 'react';

// Arrow Icon for moving ships
const createArrowIcon = (heading, color = '#2563eb') => {
    return L.divIcon({
        className: 'custom-arrow-icon',
        html: `<div style="transform: rotate(${heading}deg); width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="${color}" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="12 2 22 22 12 18 2 22 12 2" />
            </svg>
        </div>`,
        iconSize: [30, 30],
        iconAnchor: [15, 15],
    });
};

const AutoFitBounds = ({ bounds, triggerFit }) => {
    const map = useMap();
    const hasFitOnce = useRef(false);
    const boundsRef = useRef(bounds);

    useEffect(() => {
        boundsRef.current = bounds;
    }, [bounds]);

    useEffect(() => {
        if (!hasFitOnce.current && bounds && bounds.length > 0) {
            try {
                map.fitBounds(bounds, { padding: [50, 50] });
                hasFitOnce.current = true;
            } catch (e) {
                console.error("Bounds error", e);
            }
        }
    }, [bounds, map]);

    useEffect(() => {
        if (triggerFit > 0 && boundsRef.current && boundsRef.current.length > 0) {
            try {
                map.fitBounds(boundsRef.current, { padding: [50, 50] });
            } catch (e) {
                console.error("Bounds error", e);
            }
        }
    }, [triggerFit, map]);

    return null;
}

// Component to handle flying to selected ship
const FlyToShip = ({ ships, selectedShipId }) => {
    const map = useMap();
    const lastFlownId = useRef(null);

    useEffect(() => {
        if (selectedShipId && ships.length > 0) {
            // Only fly if the selected ship ID has CHANGED since the last fly-to action
            // This prevents re-centering every time the ship moves (data update)
            if (selectedShipId !== lastFlownId.current) {
                const ship = ships.find(s => s.id === selectedShipId);
                if (ship && ship.latitude && ship.longitude) {
                    try {
                        map.setView([ship.latitude, ship.longitude], 10, {
                            animate: true,
                            duration: 1.5
                        });
                        lastFlownId.current = selectedShipId;
                    } catch (e) {
                        console.error("FlyTo error", e);
                    }
                }
            }
        } else {
            // Reset if no ship selected, so we can select the same one again if needed (requires deselecting first)
            // Or just keep it. If we deselect, selectedShipId passed is null/undefined.
            if (!selectedShipId) {
                lastFlownId.current = null;
            }
        }
    }, [selectedShipId, ships, map]);

    return null;
}

const MapComponent = ({
    ships = [],
    selectedShipId,
    historyPath,
    fitBoundsTrigger
}) => {

    // Filter valid ships
    const validShips = ships.filter(s => s.latitude && s.longitude);
    const bounds = validShips.map(s => [s.latitude, s.longitude]);
    const defaultCenter = [10.762622, 106.660172];

    const getShipColor = (weight) => {
        if (weight > 4000) return '#ef4444'; // Red for Big
        if (weight > 1000) return '#eab308'; // Yellow for Medium
        return '#3b82f6'; // Blue for Small
    };

    const getRefRadius = (weight) => {
        // Base size 5, scales with sqrt of weight loosely
        if (!weight) return 8;
        if (weight > 4000) return 12;
        if (weight > 1000) return 9;
        return 6;
    }

    return (
        <MapContainer center={defaultCenter} zoom={6} style={{ height: '100%', width: '100%', borderRadius: '0.75rem', zIndex: 0 }}>
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            <AutoFitBounds bounds={bounds} triggerFit={fitBoundsTrigger} />
            <FlyToShip ships={ships} selectedShipId={selectedShipId} />

            {validShips.map(ship => {
                const isMoving = ship.speed > 0.5;
                const color = getShipColor(ship.weight);

                if (isMoving) {
                    // Render Arrow
                    return (
                        <Marker
                            key={`arrow-${ship.id}`}
                            position={[ship.latitude, ship.longitude]}
                            icon={createArrowIcon(ship.heading || 0, color)}
                            opacity={selectedShipId && selectedShipId !== ship.id ? 0.6 : 1.0}
                        >
                            <Popup>
                                <div className="text-slate-900">
                                    <strong>{ship.name}</strong><br />
                                    Type: {ship.weight > 4000 ? "Heavy" : ship.weight > 1000 ? "Medium" : "Light"} ({ship.weight}t)<br />
                                    Status: Using Main Engine<br />
                                    Speed: {ship.speed?.toFixed(1)} kn<br />
                                    Heading: {ship.heading?.toFixed(0)}°
                                </div>
                            </Popup>
                        </Marker>
                    )
                } else {
                    // Render Circle
                    return (
                        <CircleMarker
                            key={`circle-${ship.id}`}
                            center={[ship.latitude, ship.longitude]}
                            pathOptions={{ color: color, fillColor: color, fillOpacity: 0.7 }}
                            radius={getRefRadius(ship.weight)}
                        >
                            <Popup>
                                <div className="text-slate-900">
                                    <strong>{ship.name}</strong><br />
                                    Type: {ship.weight > 4000 ? "Heavy" : ship.weight > 1000 ? "Medium" : "Light"} ({ship.weight}t)<br />
                                    Status: Stopped/Idling
                                </div>
                            </Popup>
                        </CircleMarker>
                    )
                }
            })}

            {historyPath && <Polyline positions={historyPath || []} color="blue" />}
        </MapContainer>
    );
};

export default MapComponent;
