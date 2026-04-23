import os

# 照片库路径。可以是 NAS / SMB 挂载目录，也可以是本地相册目录。
IMAGE_DIR = "./photos"
PHOTOS_BASE_DIR = os.environ.get("PHOTOS_ROOT", IMAGE_DIR)

# 数据库。推荐使用 MySQL；本地调试时也可以保留 SQLite 路径。
DB_PATH = "./photos.db"
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://username:password@127.0.0.1:3306/poetlens"
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_recycle": 280,
    "pool_pre_ping": True,
}

# 本地视觉大模型接口，例如 LM Studio 的 OpenAI 兼容接口。
API_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL_NAME = "qwen3-vl-32b-instruct"
API_KEY = ""

# 批量分析控制。
BATCH_LIMIT = None
TIMEOUT = 600
MEMORY_THRESHOLD = 70.0

# Web 服务。
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 8765
ENABLE_REVIEW_WEBUI = True

# 受保护静态资源访问密钥。请在正式部署时替换为随机字符串。
DOWNLOAD_KEY = "replace-with-a-random-secret"

# 离线中文城市名索引，使用 geonames 数据制作。
WORLD_CITIES_CSV = "./data/world_cities_zh.csv"
CITY_GRID_DEG = 1.0
CITY_MAX_DISTANCE_KM = 100.0

# 常驻地坐标，用于判断照片是否来自旅行期间，并对评分进行小幅加成。
# 默认值给了深圳市中心附近；你可以按自己的常驻地修改。
HOME_LAT = 22.543096
HOME_LON = 114.057865
HOME_RADIUS_KM = 60.0

# 渲染输出和字体。多数网页使用场景可以保持默认。
BIN_OUTPUT_DIR = "./output"
FONT_PATH = ""
DAILY_PHOTO_QUANTITY = 5
