from database import SessionLocal
import models, crud, schemas
from datetime import datetime, timedelta
import random
import math

# Constants
MINUTES_PER_POINT = 10 # Generate data every 10 mins to keep volume manageable (30 days * 144 points/day = ~4300 points)
TOTAL_DAYS = 30
TOTAL_MINUTES = TOTAL_DAYS * 24 * 60

# Ports locations (Lat, Lon) - simplified around Vietnam coast
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

def seed_30_days():
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

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=TOTAL_DAYS)

        for ship in created_ships:
            print(f"Generating 30-day history for {ship.name}...")
            
            # Initial State
            current_time = start_time
            current_port_idx = random.randint(0, len(PORTS)-1)
            next_port_idx = (current_port_idx + 1) % len(PORTS)
            
            state = "AT_PORT" # AT_PORT, AT_SEA, REFUELING
            state_duration_left = random.randint(6*60, 12*60) # mins
            
            # Trip info
            trip_progress = 0
            trip_duration = 0
            
            points_batch = []
            
            while current_time < end_time:
                # 1. Update State Logic if duration expired
                if state_duration_left <= 0:
                    if state == "AT_PORT":
                        # Depart
                        state = "AT_SEA"
                        # Trip duration 12-24 hours
                        trip_duration = random.randint(12*60, 24*60)
                        state_duration_left = trip_duration
                        trip_progress = 0
                        # Determine if we will refuel this trip mid-way
                        will_refuel = random.choice([True, False])
                        refuel_at_progress = random.uniform(0.3, 0.7) if will_refuel else -1
                        
                    elif state == "AT_SEA":
                        # Arrived
                        state = "AT_PORT"
                        current_port_idx = next_port_idx
                        next_port_idx = (current_port_idx + random.randint(1, len(PORTS)-1)) % len(PORTS)
                        state_duration_left = random.randint(6*60, 12*60)
                        
                    elif state == "REFUELING":
                        # Resume trip
                        state = "AT_SEA"
                        # Duration is whatever is left of the trip
                        # We handled the pause in loop, so just switch back
                        pass

                # 2. Generate Data Point based on State
                lat, lon = PORTS[current_port_idx]["lat"], PORTS[current_port_idx]["lon"]
                rpm, speed, fuel = 0, 0, 0
                
                if state == "AT_PORT":
                    # Stationary, Low RPM (Idling/Generator), Low Fuel
                    rpm = random.uniform(0, 400)
                    speed = 0
                    fuel = random.uniform(5, 20)
                    # Tiny GPS jitter
                    lat += random.uniform(-0.0001, 0.0001)
                    lon += random.uniform(-0.0001, 0.0001)
                    
                elif state == "AT_SEA":
                    # Check for refueling trigger
                    if trip_progress >= refuel_at_progress and refuel_at_progress > 0:
                        state = "REFUELING"
                        state_duration_left = 30 # 30 mins refueling
                        refuel_at_progress = -1 # Consumed
                        continue # Skip to next loop iteration which will handle Refueling logic next

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
                    # segment is MINUTES_PER_POINT
                    # total trip duration is trip_duration (in mins)
                    # progress increment = MINUTES_PER_POINT / trip_duration
                    inc = MINUTES_PER_POINT / trip_duration
                    trip_progress += inc
                    if trip_progress >= 1.0:
                        trip_progress = 1.0
                        state_duration_left = 0 # Force arrival

                elif state == "REFUELING":
                    # Stationary at sea
                    # Position is wherever we were when we stopped
                    start_p = PORTS[current_port_idx]
                    end_p = PORTS[next_port_idx]
                    lat, lon = interpolate_pos(start_p, end_p, trip_progress)
                    
                    rpm = 0
                    speed = 0
                    fuel = 0 # No consumption while fueling (or very low)
                
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
                
                # Batch insert every 1000 points
                if len(points_batch) >= 1000:
                    db.add_all(points_batch)
                    db.commit()
                    points_batch = []
                
                # Advance Time
                current_time += timedelta(minutes=MINUTES_PER_POINT)
                if state != "AT_SEA": # For Port and Refueling, we explicitly count down duration
                    state_duration_left -= MINUTES_PER_POINT

            # Final commit
            if points_batch:
                db.add_all(points_batch)
                db.commit()
            
        print("30-day simulation completed!")

    except Exception as e:
        print(f"Error seeding data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_30_days()
