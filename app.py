from flask import Flask, render_template, send_file, request, abort, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import config
import os
from pathlib import Path
import urllib.parse

app = Flask(__name__)
app.config.from_object(config)
db = SQLAlchemy(app)


def _safe_join_photos(filename):
    base_dir = Path(app.config.get('PHOTOS_BASE_DIR', '') or '.').resolve()
    target = (base_dir / filename).resolve()
    if base_dir != target and base_dir not in target.parents:
        raise ValueError("path traversal blocked")
    return target

@app.route('/')
def index():
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    try:
        # Get total count
        count_result = db.session.execute(text('SELECT COUNT(*) FROM image_analysis'))
        total_items = count_result.scalar()
        total_pages = (total_items + per_page - 1) // per_page
        
        # Get paged photos
        result = db.session.execute(
            text('SELECT * FROM image_analysis ORDER BY timestamp DESC LIMIT :limit OFFSET :offset'),
            {'limit': per_page, 'offset': offset}
        )
        photos = result.mappings().all()
    except Exception as e:
        print(f"DB Error: {e}")
        photos = []
        total_pages = 0
        
    return render_template('index.html', photos=photos, page=page, total_pages=total_pages)

@app.route('/photo/<int:photo_id>/delete', methods=['POST'])
def delete_photo(photo_id):
    # MySQL table must have an 'id' column or we map rowid if we strictly migrated schema.
    # Assuming we will add 'id' column to MySQL schema in analyze_local script.
    # For now, we assume schema compatibility or use Primary Key 'path' if ID is missing?
    # But route uses int:photo_id. 
    # If the new schema uses 'id' INT AUTO_INCREMENT, we are good.
    try:
        db.session.execute(text('DELETE FROM image_analysis WHERE id = :id'), {'id': photo_id})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': str(e)}
        
    return {'success': True}

@app.route('/photo/<int:photo_id>')
def photo_detail(photo_id):
    print(f"DEBUG: Requesting photo detail for ID: {photo_id}", flush=True)
    try:
        photo = db.session.execute(text('SELECT * FROM image_analysis WHERE id = :id'), {'id': photo_id}).mappings().fetchone()
        if not photo:
             print("DEBUG: Photo not found in DB", flush=True)
             return abort(404)
    except Exception as e:
        print(f"DEBUG: DB Error in photo_detail: {e}", flush=True)
        return abort(404)
        
    # Convert RowMapping to dict to allow modification
    photo_dict = dict(photo)
    
    # 1. Try to get EXIF from DB (if valid)
    import json
    exif_data = {}
    db_exif_valid = False
    
    if photo_dict.get('exif_json'):
        try:
            exif_data = json.loads(photo_dict['exif_json'])
            if exif_data and isinstance(exif_data, dict) and len(exif_data) > 0:
                db_exif_valid = True
        except:
            pass
            
    # 2. If DB EXIF is missing, try Realtime Read
    if not db_exif_valid:
        try:
            # Construct full path
            db_path = photo_dict['path']
            base_dir = app.config.get('PHOTOS_BASE_DIR', '')
            p = Path(db_path)
            parts = p.parts
            if parts[0].endswith(':\\') or parts[0].endswith(':'):
                 rel_path = Path(*parts[1:])
            elif parts[0] == '/' or parts[0] == '\\':
                 rel_path = Path(*parts[1:])
            else:
                 rel_path = p
            full_path = os.path.join(base_dir, rel_path)
            
            if os.path.exists(full_path):
                from PIL import Image, ExifTags
                with Image.open(full_path) as img:
                    exif_raw = img.getexif()
                    if exif_raw:
                        # Basic mapping
                        # Model: 272, Make: 271, FNumber: 33437, ISOSpeedRatings: 34855, ExposureTime: 33434, FocalLength: 37386
                        # Mapping tags
                        tags = {v: k for k, v in ExifTags.TAGS.items()}
                        
                        def get_tag(name):
                            tid = tags.get(name)
                            if tid and tid in exif_raw:
                                return exif_raw[tid]
                            return None

                        make = get_tag('Make')
                        model = get_tag('Model')
                        photo_dict['exif_model'] = f"{make or ''} {model or ''}".strip()
                        
                        iso = get_tag('ISOSpeedRatings')
                        photo_dict['exif_iso'] = str(iso) if iso else None
                        
                        f_len = get_tag('FocalLength')
                        photo_dict['exif_focal_length'] = str(f_len) if f_len else None
                        
                        f_num = get_tag('FNumber')
                        photo_dict['exif_f_number'] = str(f_num) if f_num else None
                        
                        exp = get_tag('ExposureTime')
                        photo_dict['exif_exposure_time'] = str(exp) if exp else None
                        
                        dt = get_tag('DateTimeOriginal') or get_tag('DateTime')
                        if dt and not photo_dict.get('timestamp'):
                             photo_dict['timestamp'] = str(dt)
        except Exception as e:
            print(f"DEBUG: Realtime EXIF read failed: {e}", flush=True)

    # 3. Populate from JSON if we had it (DB priority or processed above?)
    # Actually if we read realtime, we populated photo_dict direct.
    # If we have DB data, use it now.
    if db_exif_valid:
        photo_dict['exif_model'] = f"{exif_data.get('make', '')} {exif_data.get('model', '')}".strip()
        photo_dict['exif_focal_length'] = exif_data.get('focal_length')
        photo_dict['exif_f_number'] = exif_data.get('f_number')
        photo_dict['exif_iso'] = exif_data.get('iso')
        photo_dict['exif_exposure_time'] = exif_data.get('exposure_time')
        if exif_data.get('datetime'):
             photo_dict['taken_at'] = exif_data.get('datetime')

    # Fallback for timestamp display
    if photo_dict.get('timestamp'):
        photo_dict['timestamp'] = str(photo_dict['timestamp'])
    
    # Get next/prev for navigation
    # Using 'id' column
    next_photo = db.session.execute(text('SELECT id FROM image_analysis WHERE id > :id ORDER BY id ASC LIMIT 1'), {'id': photo_id}).mappings().fetchone()
    prev_photo = db.session.execute(text('SELECT id FROM image_analysis WHERE id < :id ORDER BY id DESC LIMIT 1'), {'id': photo_id}).mappings().fetchone()
    
    return render_template('detail.html', photo=photo_dict, next_id=next_photo['id'] if next_photo else None, prev_id=prev_photo['id'] if prev_photo else None)

@app.route('/image/<int:photo_id>')
def serve_image(photo_id):
    row = db.session.execute(text('SELECT path FROM image_analysis WHERE id = :id'), {'id': photo_id}).mappings().fetchone()
    
    if row:
        db_path = row['path']
        base_dir = app.config.get('PHOTOS_BASE_DIR', '')
        
        # Handle path joining carefully.
        # If db_path is 'E:/...' and base is 'Z:/', join fails on Windows if both absolute-like.
        # Strategy: Strip drive letter from db_path if present, then join.
        # This assumes db_path is meant to be relative to the new base.
        
        # Normalize slashes
        p = Path(db_path)
        # remove drive if exists (e.g. E:)
        parts = p.parts
        if parts[0].endswith(':\\') or parts[0].endswith(':'):
             # Remove drive letter, keep the rest
             # e.g. ('E:\\', 'test', 'a.jpg') -> ('test', 'a.jpg')
             rel_path = Path(*parts[1:])
        elif parts[0] == '/' or parts[0] == '\\':
             rel_path = Path(*parts[1:])
        else:
             rel_path = p
             
        full_path = os.path.join(base_dir, rel_path)
        
        print(f"DEBUG: PhotoID={photo_id} | Base={base_dir} | DB={db_path} | Rel={rel_path} | Full={full_path} | Exists={os.path.exists(full_path)}", flush=True)
        
        if os.path.exists(full_path):
             try:
                import mimetypes
                mt, _ = mimetypes.guess_type(full_path)
                return send_file(full_path, mimetype=mt)
             except Exception as e:
                print(f"DEBUG: send_file failed: {e}", flush=True)
                return abort(500)
        else:
             # Fallback: try original path just in case
             if os.path.exists(db_path):
                  try:
                     import mimetypes
                     mt, _ = mimetypes.guess_type(db_path)
                     return send_file(db_path, mimetype=mt)
                  except Exception as e:
                     print(f"DEBUG: fallback send_file failed: {e}", flush=True)
                     return abort(500)
                  
             print(f"Image not found: Constructed: {full_path} | Original: {db_path}", flush=True)
             return abort(404)
    else:
        return abort(404)


@app.route('/nas_photos/<path:filename>')
def serve_nas_photo(filename):
    # 解码中文路径（例如 %E6%89... -> 手机备份）
    decoded_filename = urllib.parse.unquote(filename)
    try:
        full_path = _safe_join_photos(decoded_filename)
    except ValueError:
        return abort(400)
    
    # 打印日志方便调试
    if not full_path.exists():
        return abort(404)

    return send_from_directory(str(full_path.parent), full_path.name)

if __name__ == '__main__':
    app.run(
        host=app.config.get('FLASK_HOST', '0.0.0.0'),
        port=app.config.get('FLASK_PORT', 5000),
        debug=False,
    )
