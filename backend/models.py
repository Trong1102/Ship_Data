from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    ships = relationship("UserShip", back_populates="user")

class Ship(Base):
    __tablename__ = "ships"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    mmsi = Column(String, unique=True, index=True)
    weight = Column(Float, default=1000.0)
    users = relationship("UserShip", back_populates="ship")
    telemetry = relationship("Telemetry", back_populates="ship")

class UserShip(Base):
    __tablename__ = "user_ships"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    ship_id = Column(Integer, ForeignKey("ships.id"), primary_key=True)
    user = relationship("User", back_populates="ships")
    ship = relationship("Ship", back_populates="users")

class Telemetry(Base):
    __tablename__ = "telemetry"
    id = Column(Integer, primary_key=True, index=True)
    ship_id = Column(Integer, ForeignKey("ships.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    rpm = Column(Float)
    speed = Column(Float)
    fuel_consumption = Column(Float)
    latitude = Column(Float)
    longitude = Column(Float)
    heading = Column(Float, default=0.0)
    ship = relationship("Ship", back_populates="telemetry")
