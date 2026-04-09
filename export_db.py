
import sqlite3
import pandas as pd
import json
import argparse
from pathlib import Path

DB_PATH = Path("local_photos.db").resolve()

def export_data(format="csv"):
    if not DB_PATH.exists():
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    
    # Read data
    try:
        # Select all columns explicitly to ensure order
        query = """
        SELECT path, description, type, memory_score, beauty_score, reason, 
               width, height, orientation, exif_datetime, exif_make, exif_model,
               exif_iso, exif_exposure_time, exif_f_number, exif_focal_length,
               exif_gps_lat, exif_gps_lon, exif_gps_alt, timestamp
        FROM image_analysis
        """
        df = pd.read_sql_query(query, conn)
    except Exception as e:
         print(f"Warning: Could not select all columns ({e}). Falling back to *")
         df = pd.read_sql_query("SELECT * FROM image_analysis", conn)
    
    conn.close()

    print(f"Found {len(df)} records.")

    import time
    timestamp = int(time.time())

    try:
        if format == "excel":
            output_file = f"analysis_results_{timestamp}.xlsx"
            df.to_excel(output_file, index=False)
        elif format == "json":
            output_file = f"analysis_results_{timestamp}.json"
            df.to_json(output_file, orient="records", force_ascii=False, indent=2)
        else:
            output_file = f"analysis_results_{timestamp}.csv"
            df.to_csv(output_file, index=False, encoding="utf-8-sig")
            
        print(f"Exported to {output_file}")
        
    except PermissionError:
        print(f"Error: Could not write to file. Please check if it's open.")
        return

    # Print first few rows
    print("\nPreview (Top 5):")
    for index, row in df.head().iterrows():
        print(f"--- Image: {Path(row['path']).name} ---")
        if 'memory_score' in row:
            print(f"Score: {row['memory_score']} | Type: {row['type']}")
        print(f"Desc: {str(row['description'])[:100]}...") 
        print("")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export database content")
    parser.add_argument("--format", choices=["csv", "json", "excel"], default="csv", help="Output format")
    args = parser.parse_args()
    
    try:
        export_data(args.format)
    except ImportError:
        print("Pandas/OpenPyXL not installed. Installing...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "openpyxl"])
        export_data(args.format)
