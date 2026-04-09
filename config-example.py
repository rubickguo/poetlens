# 照片库路径（你自己的相册目录）
IMAGE_DIR = "./test"

# 数据库路径（建议保持默认）
DB_PATH = "./photos.db"

# VLM 模型接口（如 LM Studio）
API_URL = "http://127.0.0.1:1234/v1/chat/completions"
import os

IMAGE_DIR = "./photos"
PHOTOS_BASE_DIR = os.environ.get("PHOTOS_ROOT", IMAGE_DIR)
SQLALCHEMY_DATABASE_URI = "mysql+pymysql://username:password@127.0.0.1:3306/poetlens"
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_recycle": 280,
    "pool_pre_ping": True,
}
DB_PATH = "./photos.db"
API_URL = "http://127.0.0.1:1234/v1/chat/completions"
BATCH_LIMIT = None
TIMEOUT = 600
DOWNLOAD_KEY = "replace-with-a-random-secret"
FLASK_HOST = "0.0.0.0"
ENABLE_REVIEW_WEBUI = True
CITY_GRID_DEG = 1.0
CITY_MAX_DISTANCE_KM = 100.0
MEMORY_THRESHOLD = 70.0

MODEL_NAME = "qwen3-vl-32b-instruct"
API_KEY = ""

# 每次最多处理多少张的图片
BATCH_LIMIT = None

# 请求超时时间（秒）
TIMEOUT = 600

# 为防止照片隐私泄露，建议为 ESP32 下载路径加一个随机前缀作为密钥
# 前缀修改后，请同步修改 esp32/ink-display-7C-photo/ink-display-7C-photo.ino 固件中的 DAILY_PHOTO_PATH_PREFIX 字段）
DOWNLOAD_KEY = "yourdownloadkey"

# Flask 静态服务
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 8765
# 是否开启照片库 WebUI（前期检验提示词选片效果时使用，跑通后建议关闭）
ENABLE_REVIEW_WEBUI = True

# 离线中文城市名索引，使用 geonames 数据制作
WORLD_CITIES_CSV = "./data/world_cities_zh.csv"

# 网格大小（纬度/经度度数）；越大越快但精度略差。1.0 对大多数场景够用。
CITY_GRID_DEG = 1.0

# 你的“常驻常驻”坐标（用于判断是否为旅行期间照片，从而对评分进行小幅加成）
# 照片 GPS 距离常驻地超过 HOME_RADIUS_KM，则视为“异地”
# 默认值给了深圳市中心附近（不改也能保持原行为的大致效果）
HOME_LAT = 22.543096
HOME_LON = 114.057865
HOME_RADIUS_KM = 60.0

# 最大接受距离（公里），超出则认为“不在任何城市附近”
CITY_MAX_DISTANCE_KM = 100.0

# 墨水屏渲染 BIN 文件输出目录
BIN_OUTPUT_DIR = "./output"

# 自定义字体路径（为空则退回默认字体）
FONT_PATH = ""

# 每日选片“精彩度”阈值
MEMORY_THRESHOLD = 70.0

# 每日挑选的照片数量
DAILY_PHOTO_QUANTITY = 5
