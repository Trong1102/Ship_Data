import requests
import time
import random
import math
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000"
SHIPS = [
    {"name": "Realtime Dredger A", "mmsi": "REAL001", "weight": 4500.0},
    {"name": "Realtime Cargo B", "mmsi": "REAL002", "weight": 1500.0}
]

# Create Ships first to ensure weight is set
def register_ships():
    for ship in SHIPS:
        try:
            payload = {"name": ship["name"], "mmsi": ship["mmsi"], "weight": ship["weight"]}
            requests.post(f"{API_URL}/ships/", json=payload)
        except:
            pass # Ignore if already exists

positions = {
    "REAL001": {"lat": 10.762622, "lon": 106.660172},
    "REAL002": {"lat": 10.34599, "lon": 107.08426}
}

vectors = {
    "REAL001": {"d_lat": -0.0005, "d_lon": 0.0005}, 
    "REAL002": {"d_lat": 0.0005, "d_lon": -0.0005}  
}

def calculate_heading(lat1, lon1, lat2, lon2):
    # Simple bearing calculation
    dLon = (lon2 - lon1)
    y = math.sin(dLon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLon)
    brng = math.atan2(y, x)
    return (math.degrees(brng) + 360) % 360

def simulate():
    register_ships()
    print(f"Starting advanced simulation for {len(SHIPS)} ships...")
    
    while True:
        for ship in SHIPS:
            mmsi = ship["mmsi"]
            pos = positions[mmsi]
            vec = vectors[mmsi]
            
            old_lat, old_lon = pos["lat"], pos["lon"]
            
            # Update Position
            pos["lat"] += vec["d_lat"] + random.uniform(-0.0001, 0.0001)
            pos["lon"] += vec["d_lon"] + random.uniform(-0.0001, 0.0001)
            
            # Calculate Heading
            heading = calculate_heading(math.radians(old_lat), math.radians(old_lon), math.radians(pos["lat"]), math.radians(pos["lon"]))
            
            # Simulate Data
            rpm = random.uniform(1800, 2200)
            speed = random.uniform(10, 15)
            fuel = rpm * 0.1 + speed * 2 + random.uniform(-5, 5)
            
            payload = {
                "rpm": rpm,
                "speed": speed,
                "fuel_consumption": fuel,
                "latitude": pos["lat"],
                "longitude": pos["lon"],
                "heading": heading
            }
            
            try:
                # Send Data
                url = f"{API_URL}/telemetry/{mmsi}"
                requests.post(url, json=payload)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {ship['name']} -> Sent (Heading: {int(heading)}°)")
            except Exception as e:
                print(f"Connection Error: {e}")
        
        # Wait 30 seconds before next update
        time.sleep(30)

if __name__ == "__main__":
    simulate()