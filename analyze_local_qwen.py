
import os
import sys
import os
import sys
import argparse
import base64
import time
import io
import json
import requests
from pathlib import Path
from PIL import Image
from sqlalchemy import create_engine, text
import config


# =======================
# Configuration
# =======================
API_URL = "http://127.0.0.1:1234/v1/chat/completions"
# DB setup
try:
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI, **config.SQLALCHEMY_ENGINE_OPTIONS)
except Exception as e:
    print(f"Failed to create DB engine: {e}")
    sys.exit(1)
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
# Model name to send in API request - usually ignored by local servers or needs to match loaded model
API_MODEL_NAME = "qwen" 

# Check for exiftool availability (simplified check)
EXIFTOOL_AVAILABLE = False
try:
    import subprocess
    subprocess.run(["exiftool", "-ver"], capture_output=True, check=True)
    EXIFTOOL_AVAILABLE = True
except Exception:
    pass


SYSTEM_PROMPT = (
    "你是一个“个人相册照片评估助手”兼“网页照片文案专家”。\n"
    "你的任务包含两部分：\n"
    "第一部分：专业的照片分析与打分（用于归档和筛选）。\n"
    "第二部分：创作一句适合网页画廊展示的中文旁白（用于展示）。\n\n"

    "【一、详细分析任务】\n"
    "1）用中文详细描述照片内容（80~200 字）。\n"
    "2）判断照片的大致类型：人物/孩子/猫咪/家庭/旅行/风景/美食/宠物/日常/文档/杂物/其他。\n"
    "3）给出 0~100 的“值得回忆度” memory_score（精确到一位小数）。\n"
    "4）给出 0~100 的“美观程度” beauty_score（精确到一位小数）。\n"
    "5）用简短中文 reason 解释评分原因（不超过 40 字）。\n\n"

    "【评分标准参考】\n"
    "- memory_score：无意义/模糊/截图 < 40； 孩子/宠物/重要合影/决定性瞬间 > 75； 普通旅游/风景 ~65。\n"
    "- beauty_score：构图好/光影美/色彩佳 > 80； 随手拍/杂乱 ~60。\n\n"

    "【二、文案创作任务（one_sentence_copy）】\n"
    "你现在的身份是为「网页照片画廊」撰写旁白短句的中文文案助手。\n"
    "你的目标不是描述画面，而是为画面补上一点“画外之意”。\n"
    "创作原则：\n"
    "1. 避免使用以下词语：世界、梦、时光、岁月、温柔、治愈、刚刚好、悄悄、慢慢 等（但不是绝对禁止）。\n"
    "2. 严禁使用如下句式：……里……着整个世界；……里……着整个夏天；……得像……（简单的比喻）; ……比……还……； ……得比……更……。\n"
    "3. 只基于图片中能确定的信息进行联想，不要虚构时间、人物关系、事件背景。\n"
    "4. 文案应自然、有趣，带一点幽默或者诗意，但请避免煽情、鸡汤。\n"
    "5. 不要复述画面内容本身，而是写“看完画面后，心里多出来的一句话”。\n"
    "6. 可以偏向以下风格之一：\n"
    "   - 日常中的微妙情绪\n"
    "   - 轻微自嘲或冷幽默\n"
    "   - 对时间、记忆、瞬间的含蓄感受\n"
    "   - 看似平淡但有余味的一句判断\n"
    "7. 避免小学生作文式的、套路式的模板化表达\n"
    "格式要求：\n"
    "1. 只输出一句中文短句，不要换行，不要引号，不要任何解释。\n"
    "2. 建议长度 8～24 个汉字，最多不超过 30 个汉字。\n"
    "3. 不要出现“这张照片”“这一刻”“那天”等指代照片本身的词。\n\n"

    "请严格只输出 JSON，格式如下：\n"
    "{\n"
    "  \"caption\": \"……\",\n"
    "  \"type\": \"……\",\n"
    "  \"memory_score\": 0.0,\n"
    "  \"beauty_score\": 0.0,\n"
    "  \"reason\": \"……\",\n"
    "  \"one_sentence_copy\": \"这里填你创作的那句文案\"\n"
    "}\n"
    "不要输出任何多余文字，不要加注释。"
)

def init_db():
    """Initialize MySQL database with full schema including one_sentence_copy."""
    try:
        with engine.connect() as conn:
            # Create main table if not exists with MySQL syntax
            # Using ID as Auto Inc PK, Path as Unique
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS image_analysis (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    path VARCHAR(500) UNIQUE,
                    description TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    meta_json TEXT,
                    type TEXT,
                    memory_score REAL,
                    beauty_score REAL,
                    reason TEXT,
                    one_sentence_copy TEXT,
                    width INTEGER,
                    height INTEGER,
                    orientation TEXT,
                    exif_datetime TEXT,
                    exif_make TEXT,
                    exif_model TEXT,
                    exif_iso INTEGER,
                    exif_exposure_time REAL,
                    exif_f_number REAL,
                    exif_focal_length REAL,
                    exif_gps_lat REAL,
                    exif_gps_lon REAL,
                    exif_gps_alt REAL,
                    exif_city TEXT,
                    exif_json TEXT
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """))
            conn.commit()
    except Exception as e:
        print(f"DB Init Error: {e}")

def is_processed(path):
    with engine.connect() as conn:
        try:
            result = conn.execute(text("SELECT 1 FROM image_analysis WHERE path = :path AND one_sentence_copy IS NOT NULL"), {"path": str(path)}).fetchone()
            return result is not None
        except Exception as e:
            # print(f"Check error: {e}")
            return False

def _convert_gps_to_deg(value):
    try:
        d, m, s = value
        return float(d[0]) / float(d[1]) + float(m[0]) / float(m[1]) / 60.0 + float(s[0]) / float(s[1]) / 3600.0
    except Exception:
        return None

def read_gps_with_exiftool(path: Path):
    if not EXIFTOOL_AVAILABLE:
        return None
    try:
        result = subprocess.run(
            ["exiftool", "-n", "-json", str(path)],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return None

    try:
        data = json.loads(result.stdout)[0]
    except Exception:
        return None

    lat = data.get("GPSLatitude")
    lon = data.get("GPSLongitude")
    alt = data.get("GPSAltitude")
    if lat is None or lon is None:
        return None
    return {
        "lat": float(lat),
        "lon": float(lon),
        "alt": float(alt) if alt is not None else None,
    }

def read_exif(path: Path) -> dict:
    from PIL import ExifTags
    info: dict = {}
    try:
        img = Image.open(path)
        try:
            width, height = img.size
            info["width"] = int(width)
            info["height"] = int(height)
            if width > height:
                info["orientation"] = "landscape"
            elif height > width:
                info["orientation"] = "portrait"
            else:
                info["orientation"] = "square"
        except Exception:
            pass
        exif_raw = img._getexif() or {}
    except Exception:
        return info

    exif = {}
    for tag_id, value in exif_raw.items():
        tag = ExifTags.TAGS.get(tag_id, tag_id)
        exif[tag] = value

    # Basic fields
    info["datetime"] = exif.get("DateTimeOriginal") or exif.get("DateTime")
    info["make"] = exif.get("Make")
    info["model"] = exif.get("Model")
    info["iso"] = exif.get("ISOSpeedRatings") or exif.get("PhotographicSensitivity")
    info["exposure_time"] = exif.get("ExposureTime")
    info["f_number"] = exif.get("FNumber")
    info["focal_length"] = exif.get("FocalLength")

    gps_info = exif.get("GPSInfo")
    lat = lon = None
    if isinstance(gps_info, dict):
        gps_tags = {}
        for k, v in gps_info.items():
            name = ExifTags.GPSTAGS.get(k, k)
            gps_tags[name] = v

        lat_ref = gps_tags.get("GPSLatitudeRef")
        lat_raw = gps_tags.get("GPSLatitude")
        lon_ref = gps_tags.get("GPSLongitudeRef")
        lon_raw = gps_tags.get("GPSLongitude")

        if lat_raw and lat_ref:
            lat = _convert_gps_to_deg(lat_raw)
            if lat is not None and lat_ref in ["S", "s"]:
                lat = -lat
        if lon_raw and lon_ref:
            lon = _convert_gps_to_deg(lon_raw)
            if lon is not None and lon_ref in ["W", "w"]:
                lon = -lon

    info["gps_lat"] = lat
    info["gps_lon"] = lon

    if info.get("gps_lat") is None or info.get("gps_lon") is None:
        gps = read_gps_with_exiftool(path)
        if gps is not None:
            info["gps_lat"] = gps["lat"]
            info["gps_lon"] = gps["lon"]
            if gps.get("alt") is not None:
                info["gps_alt"] = gps["alt"]

    return info

def save_result(path, result_dict, exif_info, meta=None):
    caption = result_dict.get("caption", "")
    type_val = result_dict.get("type", "")
    if isinstance(type_val, list):
        type_str = ",".join(str(x) for x in type_val)
    else:
        type_str = str(type_val)
        
    memory_score = result_dict.get("memory_score", 0.0)
    beauty_score = result_dict.get("beauty_score", 0.0)
    reason = result_dict.get("reason", "")
    one_sentence_copy = result_dict.get("one_sentence_copy", "")
    
    # Extract EXIF fields
    width = exif_info.get("width")
    height = exif_info.get("height")
    orientation = exif_info.get("orientation")
    exif_datetime = exif_info.get("datetime")
    exif_make = exif_info.get("make")
    exif_model = exif_info.get("model")
    exif_iso = exif_info.get("iso")
    exif_exposure_time = exif_info.get("exposure_time")
    exif_f_number = exif_info.get("f_number")
    exif_focal_length = exif_info.get("focal_length")
    exif_gps_lat = exif_info.get("gps_lat")
    exif_gps_lon = exif_info.get("gps_lon")
    exif_gps_alt = exif_info.get("gps_alt")
    exif_json_str = json.dumps(exif_info, ensure_ascii=False, default=str)

    # MySQL Insert on Duplicate Update
    sql = text("""
        INSERT INTO image_analysis 
        (path, description, type, memory_score, beauty_score, reason, one_sentence_copy,
         width, height, orientation, exif_datetime, exif_make, exif_model, 
         exif_iso, exif_exposure_time, exif_f_number, exif_focal_length,
         exif_gps_lat, exif_gps_lon, exif_gps_alt, exif_json, meta_json)
        VALUES (:path, :caption, :type, :m_score, :b_score, :reason, :copy,
         :w, :h, :orient, :dt, :make, :model, :iso, :exp, :fnum, :foc,
         :lat, :lon, :alt, :ejson, :meta)
        ON DUPLICATE KEY UPDATE
        description = VALUES(description),
        type = VALUES(type),
        memory_score = VALUES(memory_score),
        beauty_score = VALUES(beauty_score),
        reason = VALUES(reason),
        one_sentence_copy = VALUES(one_sentence_copy),
        width = VALUES(width),
        height = VALUES(height),
        orientation = VALUES(orientation),
        exif_datetime = VALUES(exif_datetime),
        exif_make = VALUES(exif_make),
        exif_model = VALUES(exif_model),
        exif_iso = VALUES(exif_iso),
        exif_exposure_time = VALUES(exif_exposure_time),
        exif_f_number = VALUES(exif_f_number),
        exif_focal_length = VALUES(exif_focal_length),
        exif_gps_lat = VALUES(exif_gps_lat),
        exif_gps_lon = VALUES(exif_gps_lon),
        exif_gps_alt = VALUES(exif_gps_alt),
        exif_json = VALUES(exif_json),
        meta_json = VALUES(meta_json)
    """)
    
    params = {
        "path": str(path), "caption": caption, "type": type_str, "m_score": memory_score, 
        "b_score": beauty_score, "reason": reason, "copy": one_sentence_copy,
        "w": width, "h": height, "orient": orientation, 
        "dt": str(exif_datetime) if exif_datetime else None,
        "make": str(exif_make) if exif_make else None,
        "model": str(exif_model) if exif_model else None,
        "iso": exif_iso,
        "exp": str(exif_exposure_time) if exif_exposure_time else None,
        "fnum": str(exif_f_number) if exif_f_number else None,
        "foc": str(exif_focal_length) if exif_focal_length else None,
        "lat": exif_gps_lat, "lon": exif_gps_lon, "alt": exif_gps_alt,
        "ejson": exif_json_str,
        "meta": json.dumps(meta or {}, ensure_ascii=False)
    }
    
    try:
        with engine.begin() as conn:
            conn.execute(sql, params)
    except Exception as e:
        print(f"Save Error: {e}")

def get_image_files(root_dir):
    root = Path(root_dir)
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            if "screenshot" not in path.name.lower(): 
                yield path

import shutil
import tempfile

def encode_image_to_base64(image_path):
    # Retry logic for NAS/Network drives
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Try 1: Direct Open
            with Image.open(image_path) as img:
                return _process_image_to_b64(img)
        except (OSError, PermissionError) as e:
            # If standard open fails (common on NAS), try copying to temp
            print(f"  -> Direct read failed ({e}), attempting local temp copy...")
            try:
                with tempfile.NamedTemporaryFile(suffix=image_path.suffix, delete=False) as tmp:
                    shutil.copy2(image_path, tmp.name)
                    temp_path = Path(tmp.name)
                
                with Image.open(temp_path) as img:
                    result = _process_image_to_b64(img)
                
                # Cleanup
                try:
                    os.unlink(temp_path)
                except:
                    pass
                return result
            except Exception as copy_err:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                print(f"Error encoding image {image_path}: {e} | Copy failed: {copy_err}")
                return None
    return None

def _process_image_to_b64(img):
    """Helper to resize and stringify image"""
    max_size = 512
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size))
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
        
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=80)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def analyze_image_api(image_path):
    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        raise ValueError("Failed to encode image")

    # Read EXIF
    exif_info = read_exif(image_path)

    headers = {"Content-Type": "application/json"}
    
    payload = {
        "model": API_MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "请基于这张照片，完成分析并生成一句符合规则的中文文案。"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        "temperature": 0.4, # Slightly higher for creativity in copy
        "max_tokens": 1024,
        "stream": False
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            content = result["choices"][0]["message"]["content"]
            # Clean content if it contains markdown code blocks
            content = content.replace("```json", "").replace("```", "").strip()
            try:
                ai_result = json.loads(content)
            except json.JSONDecodeError:
                 print(f"JSON Parse Error. Raw content: {content}")
                 ai_result = {"caption": content, "type": "Unknown", "memory_score": 0, "beauty_score": 0, "reason": "JSON Parse Error", "one_sentence_copy": ""}
            
            return ai_result, exif_info
        else:
            raise ValueError(f"Invalid API response format: {result}")
            
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
             print(f"API Error ({e.response.status_code}): {e.response.text}")
        raise RuntimeError(f"API Request failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Batch analyze images using Qwen3-VL via Local API")
    parser.add_argument("root_dirs", nargs='+', help="Root directories containing images")
    parser.add_argument("--dry-run", action="store_true", help="Scan files only, do not call API")
    args = parser.parse_args()

    init_db()
    
    print("Scanning for images...")
    all_images = []
    for d in args.root_dirs:
        root_dir = Path(d)
        if not root_dir.exists():
            print(f"Warning: Directory {root_dir} does not exist. Skipping.")
            continue
        print(f"Scanning {root_dir}...")
        all_images.extend(list(get_image_files(root_dir)))
        
    print(f"Found {len(all_images)} images total.")
    
    to_process = [p for p in all_images if not is_processed(p)]
    print(f"Already processed: {len(all_images) - len(to_process)}")
    print(f"Remaining to process: {len(to_process)}")

    if args.dry_run:
        print("Dry run mode. Exiting.")
        return
        
    if not to_process:
        print("Nothing to process.")
        return

    # Check API availability (removed from original, but good to have a check)
    print(f"Checking API at {API_URL}...")
    try:
        # Simple health check (may vary by server, usually a GET to /v1/models works)
        requests.get(API_URL.replace("/chat/completions", "/models"), timeout=5)
        print("API is accessible.")
    except Exception as e:
        print(f"Warning: Could not connect to API: {e}")
        # Don't exit, might be just the models endpoint issue

    print("Starting processing...")
    success_count = 0
    error_count = 0
    
    for idx, img_path in enumerate(to_process):
        print(f"[{idx+1}/{len(to_process)}] Analyzing: {img_path.name}")
        try:
            start_time = time.time()
            result, exif_info = analyze_image_api(img_path)
            duration = time.time() - start_time
            
            save_result(img_path, result, exif_info, {"duration": duration, "api": API_URL})
            
            # Print brief summary
            desc = result.get('caption', '')[:20] + '...'
            score = result.get('memory_score', 0)
            print(f"  -> Done ({duration:.2f}s) | Score: {score} | {desc}")
            success_count += 1
            
            time.sleep(1) 
            
        except KeyboardInterrupt:
            print("\nInterrupted by user. Saving progress...")
            break
        except Exception as e:
            print(f"  -> Error: {e}")
            error_count += 1

    print(f"\nProcessing finished.")
    print(f"Success: {success_count}, Errors: {error_count}")

if __name__ == "__main__":
    main()
