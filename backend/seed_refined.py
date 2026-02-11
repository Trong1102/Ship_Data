from database import SessionLocal
import models, crud, schemas
from datetime import datetime, timedelta
import random
import math

# Constants
MINUTES_PER_POINT = 30 # User requested 30 mins per row
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

def get_distance(p1, p2):
    return math.sqrt((p1["lat"] - p2["lat"])**2 + (p1["lon"] - p2["lon"])**2)

def interpolate_pos(start, end, progress):
    lat = start["lat"] + (end["lat"] - start["lat"]) * progress
    lon = start["lon"] + (end["lon"] - start["lon"]) * progress
    return lat, lon

def seed_30_days_refined():
    db = SessionLocal()
    try:
        # Create Ships if needed
        ships_data = [
            {"name": "Sand Dredger 01", "mmsi": "123456789"},
            {"name": "Cargo Carrier 02", "mmsi": "987654321"},
        ]
        
        created_ships = []
        for s in ships_data:
            existing = crud.get_ship(db, mmsi=s["mmsi"])
            if not existing:
                ship_in = schemas.ShipCreate(name=s["name"], mmsi=s["mmsi"])
                new_ship = crud.create_ship(db, ship_in)
                created_ships.append(new_ship)
            else:
                created_ships.append(existing)

        # Clear existing telemetry to avoid duplicates/messy data for this demo
        # db.query(models.Telemetry).delete() # Risky in prod, ok for demo script? 
        # Better to just append or maybe let user know. 
        # Let's delete for these specific ships to ensure clean history visualization as requested.
        for ship in created_ships:
            db.query(models.Telemetry).filter(models.Telemetry.ship_id == ship.id).delete()
        db.commit()
        print("Cleared old data for demo ships.")

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=TOTAL_DAYS)

        for ship in created_ships:
            print(f"Generating refined 30-day history for {ship.name}...")
            
            # Initial State
            current_time = start_time
            current_port_idx = random.randint(0, len(PORTS)-1)
            next_port_idx = (current_port_idx + 1) % len(PORTS)
            
            state = "AT_PORT" 
            state_duration_left = random.randint(6*60, 12*60) # mins
            
            # Trip info
            trip_progress = 0
            trip_duration = 0
            
            # Stop logic: Stop every ~5 days
            mins_since_last_stop = 0
            stop_interval = 5 * 24 * 60 # 5 days
            
            points_batch = []
            
            while current_time < end_time:
                # 1. Update State Logic
                if state_duration_left <= 0:
                    if state == "AT_PORT":
                        # Depart
                        state = "AT_SEA"
                        # Trip duration 12-24 hours
                        trip_duration = random.randint(12*60, 24*60)
                        state_duration_left = trip_duration
                        trip_progress = 0
                        
                    elif state == "AT_SEA":
                        # Arrived
                        state = "AT_PORT"
                        current_port_idx = next_port_idx
                        next_port_idx = (current_port_idx + random.randint(1, len(PORTS)-1)) % len(PORTS)
                        state_duration_left = random.randint(6*60, 12*60)
                        
                    elif state == "STOPPED":
                        # Resume trip
                        state = "AT_SEA"
                        pass

                # CHECK FOR RARE STOP (Only if AT_SEA)
                if state == "AT_SEA" and mins_since_last_stop > stop_interval:
                    if random.random() < 0.2: # 20% chance once interval passes, effectively ensuring it happens soon
                        state = "STOPPED"
                        state_duration_left = 30 # 30 mins stop
                        mins_since_last_stop = 0

                # 2. Generate Data Point
                lat, lon = PORTS[current_port_idx]["lat"], PORTS[current_port_idx]["lon"]
                rpm, speed, fuel = 0, 0, 0
                
                if state == "AT_PORT":
                    rpm = random.uniform(0, 200)
                    speed = 0
                    fuel = random.uniform(2, 10)
                    lat += random.uniform(-0.0001, 0.0001)
                    lon += random.uniform(-0.0001, 0.0001)
                    
                    mins_since_last_stop += MINUTES_PER_POINT
                    
                elif state == "AT_SEA":
                    # Moving
                    pct = trip_progress
                    start_p = PORTS[current_port_idx]
                    end_p = PORTS[next_port_idx]
                    lat, lon = interpolate_pos(start_p, end_p, pct)
                    lat += random.uniform(-0.001, 0.001) # Small deviation
                    
                    rpm = random.uniform(1800, 2200)
                    speed = random.uniform(15, 20)
                    fuel = random.uniform(150, 250)
                    
                    # Advance trip progress
                    inc = MINUTES_PER_POINT / trip_duration
                    trip_progress += inc
                    if trip_progress >= 1.0:
                        trip_progress = 1.0
                        state_duration_left = 0 # Force arrival
                        
                    mins_since_last_stop += MINUTES_PER_POINT

                elif state == "STOPPED":
                    # Stationary at sea
                    start_p = PORTS[current_port_idx]
                    end_p = PORTS[next_port_idx]
                    lat, lon = interpolate_pos(start_p, end_p, trip_progress)
                    
                    rpm = 0
                    speed = 0
                    fuel = 0 
                    
                    # Reset counter happen when we enter state, so just increment here technically it's 0
                    mins_since_last_stop = 0
                
                # Create Object
                db_t = models.Telemetry(
                    ship_id=ship.id,
                    timestamp=current_time,
                    rpm=rpm,
                    speed=speed,
                    fuel_consumption=fuel,
                    latitude=lat,
                    longitude=lon
                )
                points_batch.append(db_t)
                
                if len(points_batch) >= 1000:
                    db.add_all(points_batch)
                    db.commit()
                    points_batch = []
                
                # Advance Time
                current_time += timedelta(minutes=MINUTES_PER_POINT)
                if state != "AT_SEA":
                    state_duration_left -= MINUTES_PER_POINT

            if points_batch:
                db.add_all(points_batch)
                db.commit()
            
        print("Refined 30-day simulation completed!")

    except Exception as e:
        print(f"Error seeding data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_30_days_refined()
