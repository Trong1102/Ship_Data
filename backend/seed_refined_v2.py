from database import SessionLocal
import models, crud, schemas
from datetime import datetime, timedelta
import random
import math

# Constants
MINUTES_PER_POINT = 30
TOTAL_DAYS = 30
TOTAL_MINUTES = TOTAL_DAYS * 24 * 60

# Ports locations
PORTS = [
    {"name": "HCMC Port", "lat": 10.762622, "lon": 106.660172},
    {"name": "Vung Tau", "lat": 10.34599, "lon": 107.08426},
    {"name": "Hai Phong", "lat": 20.844912, "lon": 106.688087},
    {"name": "Da Nang", "lat": 16.054407, "lon": 108.202167},
    {"name": "Can Tho", "lat": 10.045162, "lon": 105.746857}
]

def calculate_heading(lat1, lon1, lat2, lon2):
    # Simple bearing calculation
    dLon = (lon2 - lon1)
    y = math.sin(dLon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLon)
    brng = math.atan2(y, x)
    return (math.degrees(brng) + 360) % 360

def interpolate_pos(start, end, progress):
    lat = start["lat"] + (end["lat"] - start["lat"]) * progress
    lon = start["lon"] + (end["lon"] - start["lon"]) * progress
    return lat, lon

def seed_30_days_refined_v2():
    # Ensure tables exist
    import database
    models.Base.metadata.create_all(bind=database.engine)
    
    db = SessionLocal()
    try:
        # Create Ships with different weights
        ships_data = [
            {"name": "Sand Dredger 01", "mmsi": "123456789", "weight": 5000.0}, # Big
            {"name": "Cargo Carrier 02", "mmsi": "987654321", "weight": 2000.0}, # Medium
            {"name": "Patrol Boat 03", "mmsi": "456123789", "weight": 500.0}     # Small
        ]
        
        created_ships = []
        for s in ships_data:
            existing = crud.get_ship(db, mmsi=s["mmsi"])
            if not existing:
                ship_in = schemas.ShipCreate(name=s["name"], mmsi=s["mmsi"], weight=s["weight"])
                new_ship = crud.create_ship(db, ship_in)
                created_ships.append(new_ship)
            else:
                # Update weight if exists (hacky update)
                existing.weight = s["weight"]
                db.add(existing)
                created_ships.append(existing)

        # Clear existing telemetry
        for ship in created_ships:
            db.query(models.Telemetry).filter(models.Telemetry.ship_id == ship.id).delete()
        db.commit()
        print("Cleared old data and updated ships.")

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=TOTAL_DAYS)

        for ship in created_ships:
            print(f"Generating rich 30-day history for {ship.name}...")
            
            # Initial State
            current_time = start_time
            current_port_idx = random.randint(0, len(PORTS)-1)
            next_port_idx = (current_port_idx + 1) % len(PORTS)
            
            state = "AT_PORT" 
            state_duration_left = random.randint(6*60, 12*60) 
            
            trip_progress = 0
            trip_duration = 0
            
            # Stop logic
            mins_since_last_stop = 0
            stop_interval = 5 * 24 * 60 
            
            points_batch = []
            
            while current_time < end_time:
                # 1. Update State
                if state_duration_left <= 0:
                    if state == "AT_PORT":
                        state = "AT_SEA"
                        trip_duration = random.randint(12*60, 24*60)
                        state_duration_left = trip_duration
                        trip_progress = 0
                    elif state == "AT_SEA":
                        state = "AT_PORT"
                        current_port_idx = next_port_idx
                        next_port_idx = (current_port_idx + random.randint(1, len(PORTS)-1)) % len(PORTS)
                        state_duration_left = random.randint(6*60, 12*60)
                    elif state == "STOPPED":
                        state = "AT_SEA"
                        pass

                if state == "AT_SEA" and mins_since_last_stop > stop_interval and random.random() < 0.2:
                    state = "STOPPED"
                    state_duration_left = 30 
                    mins_since_last_stop = 0

                # 2. Generate Data
                lat, lon = PORTS[current_port_idx]["lat"], PORTS[current_port_idx]["lon"]
                rpm, speed, fuel = 0, 0, 0
                heading = 0
                
                if state == "AT_PORT":
                    rpm = random.uniform(0, 200)
                    speed = 0
                    fuel = random.uniform(2, 10)
                    lat += random.uniform(-0.0001, 0.0001)
                    lon += random.uniform(-0.0001, 0.0001)
                    heading = random.uniform(0, 360) # Resting heading
                    mins_since_last_stop += MINUTES_PER_POINT
                    
                elif state == "AT_SEA":
                    # Moving
                    pct = trip_progress
                    start_p = PORTS[current_port_idx]
                    end_p = PORTS[next_port_idx]
                    
                    # Calculate position
                    lat, lon = interpolate_pos(start_p, end_p, pct)
                    lat += random.uniform(-0.001, 0.001) 
                    
                    # Calculate Heading
                    # Look ahead slightly to get vector
                    lat_next, lon_next = interpolate_pos(start_p, end_p, pct + 0.01)
                    heading = calculate_heading(math.radians(lat), math.radians(lon), math.radians(lat_next), math.radians(lon_next))
                    
                    rpm = random.uniform(1800, 2200)
                    speed = random.uniform(15, 20)
                    fuel = random.uniform(150, 250)
                    
                    inc = MINUTES_PER_POINT / trip_duration
                    trip_progress += inc
                    if trip_progress >= 1.0:
                        trip_progress = 1.0
                        state_duration_left = 0 
                        
                    mins_since_last_stop += MINUTES_PER_POINT

                elif state == "STOPPED":
                    start_p = PORTS[current_port_idx]
                    end_p = PORTS[next_port_idx]
                    lat, lon = interpolate_pos(start_p, end_p, trip_progress)
                    
                    rpm = 0
                    speed = 0
                    fuel = 0 
                    heading = (calculate_heading(math.radians(PORTS[current_port_idx]["lat"]), 
                                               math.radians(PORTS[current_port_idx]["lon"]), 
                                               math.radians(PORTS[next_port_idx]["lat"]), 
                                               math.radians(PORTS[next_port_idx]["lon"])) + random.uniform(-10, 10)) % 360
                    
                    mins_since_last_stop = 0
                
                db_t = models.Telemetry(
                    ship_id=ship.id,
                    timestamp=current_time,
                    rpm=rpm,
                    speed=speed,
                    fuel_consumption=fuel,
                    latitude=lat,
                    longitude=lon,
                    heading=heading
                )
                points_batch.append(db_t)
                
                if len(points_batch) >= 1000:
                    db.add_all(points_batch)
                    db.commit()
                    points_batch = []
                
                current_time += timedelta(minutes=MINUTES_PER_POINT)
                if state != "AT_SEA":
                    state_duration_left -= MINUTES_PER_POINT

            if points_batch:
                db.add_all(points_batch)
                db.commit()
            
        print("Refined v2 simulation completed!")

    except Exception as e:
        print(f"Error seeding data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_30_days_refined_v2()
