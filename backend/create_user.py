from database import SessionLocal
import crud, schemas

def create_admin():
    db = SessionLocal()
    try:
        user = schemas.UserCreate(username="admin", password="password123")
        crud.create_user(db, user)
        print("User 'admin' created with password 'password123'")
    except Exception as e:
        print(f"Error (maybe user exists): {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()