
import os
import sys
from sqlalchemy import text
from app import app, db
import config

def debug():
    with app.app_context():
        # Get one row
        row = db.session.execute(text('SELECT id, path FROM image_analysis LIMIT 1')).mappings().fetchone()
        if not row:
            print("No images in DB.")
            return

        db_path = row['path']
        print(f"--- Debugging Image ID: {row['id']} ---")
        print(f"DB Path Raw: {db_path}")
        print(f"DB Path Repr: {repr(db_path)}")
        
        # Check original existence
        exists_orig = os.path.exists(db_path)
        print(f"Exists at Original Path? {exists_orig}")
        
        # Check config
        base_dir = app.config.get('PHOTOS_BASE_DIR', '')
        print(f"PHOTOS_BASE_DIR: {base_dir}")
        
        # Check constructed path
        from pathlib import Path
        p = Path(db_path)
        parts = p.parts
        if parts[0].endswith(':\\') or parts[0].endswith(':'):
             rel_path = Path(*parts[1:])
        else:
             rel_path = p
        
        full_path = os.path.join(base_dir, rel_path)
        print(f"Constructed Path: {full_path}")
        print(f"Exists at Constructed? {os.path.exists(full_path)}")
        
        if not exists_orig and not os.path.exists(full_path):
             # Try listing directory to see encoding issues
             dir_name = os.path.dirname(db_path)
             if os.path.exists(dir_name):
                 print(f"Directory {dir_name} exists. Listing:")
                 print(os.listdir(dir_name))
             else:
                 print(f"Directory {dir_name} DOES NOT exist.")

if __name__ == "__main__":
    debug()
