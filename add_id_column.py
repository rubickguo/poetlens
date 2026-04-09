
from app import app, db
from sqlalchemy import text

def add_id():
    with app.app_context():
        print("Checking for 'id' column...")
        try:
            # Check if id exists
            res = db.session.execute(text("SHOW COLUMNS FROM image_analysis LIKE 'id'")).fetchone()
            if res:
                print("'id' column already exists.")
                return

            print("Adding 'id' column (AUTO_INCREMENT PRIMARY KEY)...")
            # Note: This might take a while for 16k rows, but usually fast enough.
            db.session.execute(text("ALTER TABLE image_analysis ADD COLUMN id INT AUTO_INCREMENT PRIMARY KEY FIRST"))
            # db.session.commit() # DDL implies commit in MySQL usually
            print("Successfully added 'id' column.")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    add_id()
