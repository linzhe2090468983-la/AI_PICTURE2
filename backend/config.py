import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# AI大模型API配置
AI_MODEL_CONFIGS = {
    'wenxinyige': {  # 文心一格
        'api_key': os.getenv('WENXIN_API_KEY'),
        'secret_key': os.getenv('WENXIN_SECRET_KEY'),
        'url1': 'https://qianfan.baidubce.com/v2/images/edits',
        'url2': 'https://qianfan.baidubce.com/v2/images/generations'
    },
    'tongyiwanxiang': {  # 通义万相
        'api_key': os.getenv('TONGYI_API_KEY'),
        'base_url': os.getenv('TONGYI_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
        'image_gen_url': 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image'
    },
    'jimeng': {  # 即梦
        'api_key': os.getenv('JIMENG_API_KEY'),
        'image_gen_url': 'https://api.doubao.com/dreamina/api/v1/image_generation'
    }
}

# 配置上传和输出文件夹
UPLOAD_FOLDER = 'uploads'  # 上传的原始图片存放处
OUTPUT_FOLDER = 'outputs'  # 处理后的图片存放处
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# MySQL数据库配置
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'ai_picture_gen'),
    'charset': 'utf8mb4',
    'autocommit': True
}

# JWT配置
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', 24)) 