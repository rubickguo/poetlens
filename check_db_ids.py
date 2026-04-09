
from app import app, db
from sqlalchemy import text

def check():
    with app.app_context():
        print(f"DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Check count
        cnt = db.session.execute(text("SELECT COUNT(*) FROM image_analysis")).scalar()
        print(f"Total Rows: {cnt}")
        
        # Check first few IDs
        rows = db.session.execute(text("SELECT id, path FROM image_analysis ORDER BY id ASC LIMIT 5")).mappings().all()
        print("First 5 IDs:")
        for r in rows:
            print(f"ID: {r['id']} | Path: {r['path']}")

        # Check a high ID if exist
        rows_desc = db.session.execute(text("SELECT id, path FROM image_analysis ORDER BY id DESC LIMIT 5")).mappings().all()
        print("Last 5 IDs:")
        for r in rows_desc:
            print(f"ID: {r['id']} | Path: {r['path']}")

if __name__ == "__main__":
    check()
