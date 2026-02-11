from database import SessionLocal
import models, crud, schemas
from datetime import datetime, timedelta
import random

def seed_data_advanced():
    db = SessionLocal()
    try:
        # Create Ships
        ships_data = [
            {"name": "Sand Dredger 01", "mmsi": "123456789"},
            {"name": "Cargo Carrier 02", "mmsi": "987654321"},
            {"name": "Patrol Boat 03", "mmsi": "456123789"}
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

        base_lat = 10.762622
        base_lon = 106.660172
        
        # Scenarios mapping
        # 0-20 mins ago: Unloaded (Fast return)
        # 20-40 mins ago: Loaded (Heavy, high fuel, slower)
        # 40-60 mins ago: Stopped (Idling/Loading)
        
        for ship in created_ships:
            print(f"Generating advanced data for {ship.name}...")
            
            for i in range(60): # 60 minutes of data
                minute_offset = 60 - i # 60 mins ago to now
                timestamp = datetime.utcnow() - timedelta(minutes=minute_offset)
                
                # Determine State
                if i < 20: # First 20 mins of loop (Older data) -> STOPPED
                    state = "STOPPED"
                    rpm = random.uniform(0, 600) # Idling or off
                    speed = 0
                    fuel = random.uniform(0, 10) # Minimal fuel
                    # Position stationary (with tiny GPS drift)
                    lat = base_lat + random.uniform(-0.00005, 0.00005)
                    lon = base_lon + random.uniform(-0.00005, 0.00005)
                    
                elif i < 40: # Next 20 mins -> LOADED (Heavy)
                    state = "LOADED"
                    rpm = random.uniform(1800, 2100) # High engine load
                    speed = random.uniform(6, 9) # Slower due to weight
                    fuel = random.uniform(180, 220) # High consumption
                    # Moving North
                    lat = base_lat + ((i-20) * 0.001) + random.uniform(-0.0005, 0.0005)
                    lon = base_lon + random.uniform(-0.0005, 0.0005)
                    
                else: # Last 20 mins -> UNLOADED (Return trip)
                    state = "UNLOADED"
                    rpm = random.uniform(1500, 1800) # Normal cruise
                    speed = random.uniform(12, 15) # Faster
                    fuel = random.uniform(100, 130) # Moderate
                    # Moving South (Return)
                    lat = (base_lat + (20 * 0.001)) - ((i-40) * 0.001) + random.uniform(-0.0005, 0.0005)
                    lon = base_lon + random.uniform(-0.0005, 0.0005)

                db_t = models.Telemetry(
                    ship_id=ship.id,
                    timestamp=timestamp,
                    rpm=rpm,
                    speed=speed,
                    fuel_consumption=fuel,
                    latitude=lat,
                    longitude=lon
                )
                db.add(db_t)
            
        db.commit()
        print("Advanced sample data generated successfully!")

    except Exception as e:
        print(f"Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data_advanced()
