from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TelemetryBase(BaseModel):
    rpm: float
    speed: float
    fuel_consumption: float
    latitude: float
    longitude: float
    heading: Optional[float] = 0.0

class TelemetryCreate(TelemetryBase):
    pass

class Telemetry(TelemetryBase):
    id: int
    ship_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class ShipBase(BaseModel):
    name: str
    mmsi: str
    weight: Optional[float] = 1000.0

class ShipCreate(ShipBase):
    pass

class Ship(ShipBase):
    id: int
    # telemetry: List[Telemetry] = [] 
    
    class Config:
        from_attributes = True

class ShipWithTelemetry(Ship):
    last_telemetry: Optional[Telemetry] = None

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    
    class Config:
        from_attributes = True
