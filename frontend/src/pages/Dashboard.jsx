import { useState, useEffect } from 'react';
import api from '../api';
import MapComponent from '../components/MapComponent';
import FuelChart from '../components/FuelChart';
import { Ship, Anchor, Gauge, Droplet, Navigation, History, Maximize, Calendar } from 'lucide-react';

const Dashboard = () => {
    const [ships, setShips] = useState([]);
    const [selectedShip, setSelectedShip] = useState(null);
    const [telemetry, setTelemetry] = useState([]);
    const [latestData, setLatestData] = useState(null);
    const [viewMode, setViewMode] = useState('live'); // 'live' or 'history'
    const [historyData, setHistoryData] = useState([]);
    const [fitBoundsTrigger, setFitBoundsTrigger] = useState(0);

    // Date Filter State (default to last 30 days)
    const [startDate, setStartDate] = useState(() => {
        const d = new Date();
        d.setDate(d.getDate() - 30);
        return d.toISOString().slice(0, 16); // format YYYY-MM-DDTHH:mm
    });
    const [endDate, setEndDate] = useState(() => {
        return new Date().toISOString().slice(0, 16);
    });

    // Fleet Data for Map
    const [fleetData, setFleetData] = useState([]);

    useEffect(() => {
        fetchShips();
    }, []);

    useEffect(() => {
        let interval;
        if (viewMode === 'live') {
            const fetchAll = () => {
                fetchFleetOverview();
                if (selectedShip) {
                    fetchTelemetry(selectedShip.mmsi);
                }
            };
            fetchAll();
            interval = setInterval(fetchAll, 3000);
        }
        return () => clearInterval(interval);
    }, [viewMode, selectedShip?.mmsi]);

    useEffect(() => {
        if (selectedShip) {
            if (viewMode === 'live') {
                fetchTelemetry(selectedShip.mmsi);
            } else {
                fetchHistory(selectedShip.mmsi);
            }
        }
    }, [selectedShip, viewMode, startDate, endDate]); // Re-fetch history when dates change

    const fetchShips = async () => {
        try {
            const res = await api.get('/ships/');
            setShips(res.data);
            if (res.data.length > 0 && !selectedShip) {
                setSelectedShip(res.data[0]);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const fetchFleetOverview = async () => {
        try {
            const res = await api.get('/ships/overview');
            const data = res.data.map(item => ({
                id: item.id,
                name: item.name,
                mmsi: item.mmsi,
                latitude: item.last_telemetry?.latitude,
                longitude: item.last_telemetry?.longitude,
                speed: item.last_telemetry?.speed,
                rpm: item.last_telemetry?.rpm,
                heading: item.last_telemetry?.heading,
                weight: item.weight,
                timestamp: item.last_telemetry?.timestamp
            }));
            setFleetData(data);

            if (selectedShip) {
                const shipData = res.data.find(s => s.id === selectedShip.id);
                if (shipData && shipData.last_telemetry) {
                    setLatestData(shipData.last_telemetry);
                }
            }
        } catch (err) {
            console.error(err);
        }
    };

    const fetchTelemetry = async (mmsi) => {
        try {
            const res = await api.get(`/telemetry/${mmsi}?limit=50`);
            const data = [...res.data].reverse();
            setTelemetry(data);
        } catch (err) {
            console.error(err);
        }
    };

    const fetchHistory = async (mmsi) => {
        try {
            // Convert local inputs back to ISO (or just send UTC)
            // Backend expects ISO strings, so let's ensure we send something compatible
            const startISO = new Date(startDate).toISOString();
            const endISO = new Date(endDate).toISOString();

            const res = await api.get(`/telemetry/${mmsi}?limit=5000&start_date=${startISO}&end_date=${endISO}`);
            const data = [...res.data].reverse();
            setHistoryData(data);
            // Downsample for chart happens in render, but let's check size
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="flex h-screen bg-slate-900 overflow-hidden">
            {/* Sidebar */}
            <aside className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col">
                <div className="p-6">
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Anchor className="text-blue-500" />
                        FleetMonitor
                    </h1>
                </div>
                <div className="flex-1 overflow-y-auto px-4 space-y-2">
                    {ships.map(ship => {
                        const isLive = fleetData.find(f => f.mmsi === ship.mmsi)?.speed !== undefined;
                        return (
                            <button
                                key={ship.id}
                                onClick={() => setSelectedShip(ship)}
                                className={`w-full text-left p-4 rounded-xl flex items-center gap-3 transition-all relative ${selectedShip?.id === ship.id ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20' : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'}`}
                            >
                                <div className="relative">
                                    <Ship className="w-5 h-5" />
                                    {isLive && (
                                        <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-green-500 border-2 border-slate-800 rounded-full animate-pulse"></span>
                                    )}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="font-semibold truncate">{ship.name}</div>
                                    <div className="text-xs opacity-70">MMSI: {ship.mmsi}</div>
                                </div>
                                {isLive && <span className="text-[10px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded border border-green-500/30 font-bold tracking-tighter">LIVE</span>}
                            </button>
                        );
                    })}
                    {ships.length === 0 && (
                        <div className="text-slate-500 text-sm text-center mt-10">No ships found. Start the simulator!</div>
                    )}
                </div>
                <div className="p-4 border-t border-slate-700">
                    <button onClick={() => { localStorage.removeItem('token'); window.location.reload(); }} className="w-full py-2 text-slate-400 hover:text-white text-sm transition-colors">
                        Logout
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto p-8">
                {selectedShip ? (
                    <div className="max-w-7xl mx-auto space-y-6">
                        <header className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                            <div>
                                <h2 className="text-3xl font-bold text-white">{selectedShip.name}</h2>
                                <p className="text-slate-400 flex items-center gap-2 mt-1">
                                    <span className={`w-2 h-2 rounded-full animate-pulse ${viewMode === 'live' ? 'bg-green-500' : 'bg-blue-500'}`}></span>
                                    {viewMode === 'live' ? 'Live Fleet Status' : 'History Analysis'}
                                </p>
                            </div>

                            <div className="flex flex-wrap gap-4 items-center">
                                {/* Date Filter Inputs (Only visible in History Mode) */}
                                {viewMode === 'history' && (
                                    <div className="flex items-center gap-2 bg-slate-800 p-2 rounded-lg border border-slate-700">
                                        <div className="flex items-center gap-2">
                                            <Calendar className="w-4 h-4 text-slate-400" />
                                            <input
                                                type="datetime-local"
                                                value={startDate}
                                                onChange={(e) => setStartDate(e.target.value)}
                                                className="bg-slate-700 text-white text-sm rounded px-2 py-1 outline-none focus:ring-1 focus:ring-blue-500 border border-slate-600"
                                            />
                                        </div>
                                        <span className="text-slate-400 text-sm">to</span>
                                        <div className="flex items-center gap-2">
                                            <input
                                                type="datetime-local"
                                                value={endDate}
                                                onChange={(e) => setEndDate(e.target.value)}
                                                className="bg-slate-700 text-white text-sm rounded px-2 py-1 outline-none focus:ring-1 focus:ring-blue-500 border border-slate-600"
                                            />
                                        </div>
                                    </div>
                                )}

                                <div className="flex gap-2 bg-slate-800 p-1 rounded-lg border border-slate-700">
                                    <button
                                        onClick={() => setViewMode('live')}
                                        className={`px-4 py-2 rounded-md flex items-center gap-2 text-sm font-medium transition-colors ${viewMode === 'live' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
                                    >
                                        <Gauge className="w-4 h-4" /> Live
                                    </button>
                                    <button
                                        onClick={() => setViewMode('history')}
                                        className={`px-4 py-2 rounded-md flex items-center gap-2 text-sm font-medium transition-colors ${viewMode === 'history' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
                                    >
                                        <History className="w-4 h-4" /> History
                                    </button>
                                </div>
                            </div>
                        </header>

                        {/* Top Stats */}
                        <div className="flex gap-4">
                            <div className="flex-1 bg-slate-800 p-4 rounded-xl border border-slate-700 flex items-center gap-3 shadow-lg">
                                <div className="p-2 bg-blue-500/10 rounded-lg">
                                    <Gauge className="text-blue-400" />
                                </div>
                                <div>
                                    <div className="text-slate-400 text-sm">{viewMode === 'live' ? 'Engine RPM' : 'Selected Avg RPM'}</div>
                                    <div className="text-2xl font-bold text-white">
                                        {viewMode === 'live' ? (latestData?.rpm?.toFixed(0) || 0) : '---'}
                                    </div>
                                </div>
                            </div>
                            <div className="flex-1 bg-slate-800 p-4 rounded-xl border border-slate-700 flex items-center gap-3 shadow-lg">
                                <div className="p-2 bg-green-500/10 rounded-lg">
                                    <Navigation className="text-green-400" />
                                </div>
                                <div>
                                    <div className="text-slate-400 text-sm">{viewMode === 'live' ? 'Speed (kn)' : 'Selected Avg Speed'}</div>
                                    <div className="text-2xl font-bold text-white">
                                        {viewMode === 'live' ? (latestData?.speed?.toFixed(1) || 0) : '---'}
                                    </div>
                                </div>
                            </div>
                            <div className="flex-1 bg-slate-800 p-4 rounded-xl border border-slate-700 flex items-center gap-3 shadow-lg">
                                <div className="p-2 bg-orange-500/10 rounded-lg">
                                    <Droplet className="text-orange-400" />
                                </div>
                                <div>
                                    <div className="text-slate-400 text-sm">Fuel (L/h)</div>
                                    <div className="text-2xl font-bold text-white">
                                        {viewMode === 'live' ? (latestData?.fuel_consumption?.toFixed(1) || 0) : '---'}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                            {/* Map */}
                            <div className="lg:col-span-2 bg-slate-800 p-1 rounded-xl shadow-xl border border-slate-700 h-[500px] relative">
                                <MapComponent
                                    ships={viewMode === 'live' ? fleetData : [{ ...selectedShip, ...latestData }]}
                                    selectedShipId={selectedShip.id}
                                    historyPath={viewMode === 'history' ? historyData.map(d => [d.latitude, d.longitude]) : null}
                                    fitBoundsTrigger={fitBoundsTrigger}
                                />
                                {/* Auto Fit Button */}
                                <button
                                    onClick={() => setFitBoundsTrigger(prev => prev + 1)}
                                    className="absolute bottom-4 right-4 z-[400] bg-white text-slate-900 p-2 rounded-lg shadow-lg hover:bg-slate-100 transition-colors"
                                    title="Auto-fit Map Bounds"
                                >
                                    <Maximize className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Stats/Details */}
                            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-xl h-[500px] flex flex-col">
                                <h3 className="text-xl font-semibold text-white mb-6">
                                    {viewMode === 'live' ? 'Vessel Status' : 'Period Analytics'}
                                </h3>

                                <div className="space-y-4">
                                    {viewMode === 'live' ? (
                                        <>
                                            <div className="flex justify-between items-center p-3 bg-slate-700/50 rounded-lg">
                                                <span className="text-slate-400">Status</span>
                                                <span className={`font-medium ${latestData ? 'text-green-400' : 'text-slate-500'}`}>
                                                    {latestData ? 'Underway' : 'No Signal'}
                                                </span>
                                            </div>
                                            <div className="flex justify-between items-center p-3 bg-slate-700/50 rounded-lg">
                                                <span className="text-slate-400">Last Update</span>
                                                <span className="text-white">{latestData ? new Date(latestData.timestamp).toLocaleTimeString() : '-'}</span>
                                            </div>
                                            <div className="flex justify-between items-center p-3 bg-slate-700/50 rounded-lg">
                                                <span className="text-slate-400">Coordinates</span>
                                                <span className="text-white text-sm">
                                                    {latestData ? `${latestData.latitude.toFixed(4)}, ${latestData.longitude.toFixed(4)}` : '-'}
                                                </span>
                                            </div>
                                        </>
                                    ) : (
                                        <>
                                            <div className="p-4 bg-slate-700/30 rounded-lg border border-slate-700">
                                                <div className="text-slate-400 text-xs uppercase mb-1">Data Points</div>
                                                <div className="text-white text-sm font-medium">{historyData.length} records found</div>
                                            </div>
                                            <div className="p-4 bg-slate-700/30 rounded-lg border border-slate-700">
                                                <div className="text-slate-400 text-xs uppercase mb-1">Start Time</div>
                                                <div className="text-white text-sm font-medium">{new Date(startDate).toLocaleString()}</div>
                                            </div>
                                            <div className="p-4 bg-slate-700/30 rounded-lg border border-slate-700">
                                                <div className="text-slate-400 text-xs uppercase mb-1">End Time</div>
                                                <div className="text-white text-sm font-medium">{new Date(endDate).toLocaleString()}</div>
                                            </div>
                                        </>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Chart */}
                        <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-xl">
                            <h3 className="text-xl font-semibold text-white mb-6">Fuel Consumption Analysis</h3>
                            {/* Downsample history for chart manually if too dense, but Recharts handles some. */}
                            <FuelChart data={viewMode === 'live' ? telemetry : historyData.filter((_, i) => i % Math.max(1, Math.floor(historyData.length / 100)) === 0)} />
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-slate-500">
                        <Ship className="w-24 h-24 mb-6 opacity-20" />
                        <p className="text-xl font-medium">Select a ship to view telemetry</p>
                    </div>
                )}
            </main>
        </div>
    );
};

export default Dashboard;
