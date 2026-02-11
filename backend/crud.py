from sqlalchemy.orm import Session
from datetime import datetime
import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_ship(db: Session, mmsi: str):
    return db.query(models.Ship).filter(models.Ship.mmsi == mmsi).first()

def create_ship(db: Session, ship: schemas.ShipCreate):
    db_ship = models.Ship(name=ship.name, mmsi=ship.mmsi, weight=ship.weight)
    db.add(db_ship)
    db.commit()
    db.refresh(db_ship)
    return db_ship

def get_all_ships(db: Session, skip: int = 0, limit: int = 100):
   return db.query(models.Ship).offset(skip).limit(limit).all()

def create_telemetry(db: Session, telemetry: schemas.TelemetryCreate, ship_id: int):
    db_telemetry = models.Telemetry(**telemetry.dict(), ship_id=ship_id)
    db.add(db_telemetry)
    db.commit()
    db.refresh(db_telemetry)
    return db_telemetry

def get_telemetry(db: Session, ship_id: int, limit: int = 100, start_date: datetime = None, end_date: datetime = None):
    query = db.query(models.Telemetry).filter(models.Telemetry.ship_id == ship_id)
    
    if start_date:
        query = query.filter(models.Telemetry.timestamp >= start_date)
    if end_date:
        query = query.filter(models.Telemetry.timestamp <= end_date)
        
    return query.order_by(models.Telemetry.timestamp.desc()).limit(limit).all()

def get_ships_overview(db: Session):
    ships = db.query(models.Ship).all()
    results = []
    for ship in ships:
        latest = db.query(models.Telemetry).filter(models.Telemetry.ship_id == ship.id).order_by(models.Telemetry.timestamp.desc()).first()
        results.append({
            "id": ship.id,
            "name": ship.name,
            "mmsi": ship.mmsi,
            "last_telemetry": latest
        })
    return results
