
import sqlite3
import config
from sqlalchemy import create_engine, text
import json

# Source: SQLite
SQLITE_DB = "local_photos.db"

# Destination: MySQL (from config)
MYSQL_URI = config.SQLALCHEMY_DATABASE_URI
ENGINE_OPTIONS = config.SQLALCHEMY_ENGINE_OPTIONS

def migrate():
    print(f"Reading from {SQLITE_DB}...")
    try:
        sq_conn = sqlite3.connect(SQLITE_DB)
        sq_conn.row_factory = sqlite3.Row
        sq_cursor = sq_conn.cursor()
        
        # Check table name in SQLite
        # app.py used 'image_analysis', server.py used 'photo_scores'.
        # Let's check what exists.
        tables = sq_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t['name'] for t in tables]
        print(f"Found tables in SQLite: {table_names}")
        
        src_table = None
        if 'image_analysis' in table_names:
            src_table = 'image_analysis'
        elif 'photo_scores' in table_names:
            src_table = 'photo_scores'
        
        if not src_table:
            print("No relevant table found in SQLite DB.")
            return

        print(f"Migrating table '{src_table}' to MySQL 'image_analysis'...")
        
        rows = sq_cursor.execute(f"SELECT * FROM {src_table}").fetchall()
        print(f"Read {len(rows)} rows.")
        
        sq_conn.close()
    except Exception as e:
        print(f"Error reading SQLite: {e}")
        return

    # Connect to MySQL
    print("Connecting to MySQL...")
    engine = create_engine(MYSQL_URI, **ENGINE_OPTIONS)
    
    # We assume the MySQL table 'image_analysis' is already created by analyze_local_qwen.py or manually.
    # If not, we might need to rely on init_db() logic, but let's assume existence for now or create generic.
    # Actually, analyze_local_qwen.py has init_db(). We can import it? 
    # Or just run the INSERT and hope schema matches.
    # To be safe, let's just insert.
    
    success_count = 0
    with engine.connect() as conn:
        for row in rows:
            # Convert sqlite Row to dict
            data = dict(row)
            
            # Map columns if necessary (e.g. if source is photo_scores, map to image_analysis)
            # image_analysis schema in MySQL:
            # path, description, type, memory_score, beauty_score, reason, one_sentence_copy, ...
            # exif_json, meta_json
            
            # Adjust keys for MySQL
            # If source has 'caption' instead of 'description', rename.
            if 'caption' in data and 'description' not in data:
                data['description'] = data.pop('caption')
            if 'side_caption' in data and 'one_sentence_copy' not in data:
                data['one_sentence_copy'] = data.pop('side_caption')
                
            # SQLite might have missing columns, get defaults
            params = {
                'path': data.get('path'),
                'description': data.get('description'),
                'type': str(data.get('type') or ''),
                'memory_score': data.get('memory_score'),
                'beauty_score': data.get('beauty_score'),
                'reason': data.get('reason'),
                'one_sentence_copy': data.get('one_sentence_copy'),
                'width': data.get('width'),
                'height': data.get('height'),
                'orientation': data.get('orientation'),
                'exif_datetime': data.get('exif_datetime'),
                'exif_make': data.get('exif_make'),
                'exif_model': data.get('exif_model'),
                'exif_iso': data.get('exif_iso'),
                'exif_exposure_time': data.get('exif_exposure_time'),
                'exif_f_number': data.get('exif_f_number'),
                'exif_focal_length': data.get('exif_focal_length'),
                'exif_gps_lat': data.get('exif_gps_lat'),
                'exif_gps_lon': data.get('exif_gps_lon'),
                'exif_gps_alt': data.get('exif_gps_alt'),
                'exif_json': data.get('exif_json'),
                'meta_json': data.get('meta_json'),
                'timestamp': data.get('timestamp')
            }
            
            # Insert
            try:
                # Use plain SQL or SQLAlchemy Core
                sql = text("""
                    INSERT INTO image_analysis (
                        path, description, type, memory_score, beauty_score, reason, one_sentence_copy,
                        width, height, orientation, exif_datetime, exif_make, exif_model,
                        exif_iso, exif_exposure_time, exif_f_number, exif_focal_length,
                        exif_gps_lat, exif_gps_lon, exif_gps_alt, exif_json, meta_json, timestamp
                    ) VALUES (
                        :path, :description, :type, :memory_score, :beauty_score, :reason, :one_sentence_copy,
                        :width, :height, :orientation, :exif_datetime, :exif_make, :exif_model,
                        :exif_iso, :exif_exposure_time, :exif_f_number, :exif_focal_length,
                        :exif_gps_lat, :exif_gps_lon, :exif_gps_alt, :exif_json, :meta_json, :timestamp
                    )
                    ON DUPLICATE KEY UPDATE
                        description = VALUES(description),
                        memory_score = VALUES(memory_score),
                        one_sentence_copy = VALUES(one_sentence_copy)
                """)
                conn.execute(sql, params)
                success_count += 1
            except Exception as e:
                print(f"Failed to insert {data.get('path')}: {e}")
                
        conn.commit()
    
    print(f"Migration complete. Inserted {success_count} rows.")

if __name__ == "__main__":
    migrate()
