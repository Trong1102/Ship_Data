from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import List
from jose import JWTError, jwt
import models, schemas, crud, database
from database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ship Management API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Config
SECRET_KEY = "SECRET_KEY_GOES_HERE_CHANGE_IN_PROD"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = crud.get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user

@app.post("/token", response_model=dict)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user(db, username=form_data.username)
    if not user or not crud.pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    return current_user

@app.post("/ships/", response_model=schemas.Ship)
def create_ship(ship: schemas.ShipCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    # In a real app we might check permissions here
    db_ship = crud.get_ship(db, mmsi=ship.mmsi)
    if db_ship:
        raise HTTPException(status_code=400, detail="Ship already registered")
    return crud.create_ship(db=db, ship=ship)

@app.get("/ships/", response_model=List[schemas.Ship])
def read_ships(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.get_all_ships(db, skip=skip, limit=limit)

@app.get("/ships/overview", response_model=List[schemas.ShipWithTelemetry])
def read_ships_overview(db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.get_ships_overview(db)

@app.post("/telemetry/{mmsi}", response_model=schemas.Telemetry)
def create_telemetry(mmsi: str, telemetry: schemas.TelemetryCreate, db: Session = Depends(get_db)):
    # This endpoint is for the Simulator/Arduino to push data
    # No Auth for simplicity for data ingestion? Or should we require api key?
    # For this demo, let's keep it open or require a token if simulator can send it.
    # Let's keep it open but use implicit ship creation.
    ship = crud.get_ship(db, mmsi=mmsi)
    if not ship:
        # Auto-create ship if not exists? Or error?
        # Let's auto-create for easier testing
        ship = crud.create_ship(db=db, ship=schemas.ShipCreate(name=f"Ship {mmsi}", mmsi=mmsi))
    
    return crud.create_telemetry(db=db, telemetry=telemetry, ship_id=ship.id)

@app.get("/telemetry/{mmsi}", response_model=List[schemas.Telemetry])
def get_telemetry(
    mmsi: str, 
    limit: int = 100, 
    start_date: datetime = None, 
    end_date: datetime = None, 
    db: Session = Depends(get_db), 
    current_user: schemas.User = Depends(get_current_user)
):
    ship = crud.get_ship(db, mmsi=mmsi)
    if not ship:
        raise HTTPException(status_code=404, detail="Ship not found")
    return crud.get_telemetry(db=db, ship_id=ship.id, limit=limit, start_date=start_date, end_date=end_date)
