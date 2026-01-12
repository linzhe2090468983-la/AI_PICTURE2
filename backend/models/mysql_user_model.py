"""
MySQL用户模型模块
提供基于MySQL的用户注册、登录、验证等功能
"""

import hashlib
from datetime import datetime, timedelta
import jwt
from models.database import db_connection
from config import JWT_SECRET_KEY, JWT_EXPIRATION_HOURS
import logging

logger = logging.getLogger(__name__)

class User:   # finished 
    """用户数据模型类"""

    def __init__(self, user_id=None, username=None, email=None, password_hash=None,
                 created_at=None, updated_at=None):
        """
        初始化用户对象

        Args:
            user_id (int): 用户ID
            username (str): 用户名
            email (str): 邮箱
            password_hash (str): 密码哈希值
            created_at (datetime): 创建时间
            updated_at (datetime): 更新时间
        """
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at
        self.updated_at = updated_at

class MySQLUserDB:   
    """MySQL用户数据库操作类"""

    def __init__(self):
        """
        初始化数据库连接
        使用全局数据库连接实例
        """
        self.db = db_connection

    def create_user(self, username, email, password):   # finished
        """
        创建新用户

        Args:
            username (str): 用户名
            email (str): 邮箱
            password (str): 明文密码

        Returns:
            bool: 成功返回True，失败返回False
        """
        password_hash = self._hash_password(password)

        sql = """
        INSERT INTO users (username, email, password_hash)
        VALUES (%s, %s, %s)
        """

        try:
            self.db.execute_query(sql, (username, email, password_hash), fetch=False)
            logger.info(f"用户 {username} 创建成功")
            return True
        except Exception as e:
            logger.error(f"创建用户 {username} 失败: {e}")
            return False

    def verify_user(self, username, password):   # finished
        """
        验证用户登录

        Args:
            username (str): 用户名
            password (str): 明文密码

        Returns:
            User or None: 验证成功返回User对象，失败返回None
        """
        sql = """
        SELECT id, username, email, password_hash, created_at, updated_at
        FROM users
        WHERE username = %s
        """

        try:
            results = self.db.execute_query(sql, (username,))

            if results and len(results) > 0:
                user_data = results[0]
                if self._check_password(password, user_data['password_hash']):
                    logger.info(f"用户 {username} 登录验证成功")
                    return User(
                        user_id=user_data['id'],
                        username=user_data['username'],
                        email=user_data['email'],
                        password_hash=user_data['password_hash'],
                        created_at=user_data['created_at'],
                        updated_at=user_data['updated_at']
                    )

            logger.warning(f"用户 {username} 登录验证失败")
            return None

        except Exception as e:
            logger.error(f"验证用户 {username} 时发生错误: {e}")
            return None

    def get_user_by_id(self, user_id):
        """
        根据用户ID获取用户信息

        Args:
            user_id (int): 用户ID

        Returns:
            User or None: 找到返回User对象，未找到返回None
        """
        sql = """
        SELECT id, username, email, password_hash, created_at, updated_at
        FROM users
        WHERE id = %s
        """

        try:
            results = self.db.execute_query(sql, (user_id,))

            if results and len(results) > 0:
                user_data = results[0]
                return User(
                    user_id=user_data['id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    password_hash=user_data['password_hash'],
                    created_at=user_data['created_at'],
                    updated_at=user_data['updated_at']
                )

            return None

        except Exception as e:
            logger.error(f"获取用户 {user_id} 信息时发生错误: {e}")
            return None

    def get_user_by_username(self, username):   # finished 
        """
        根据用户名获取用户信息

        Args:
            username (str): 用户名

        Returns:
            User or None: 找到返回User对象，未找到返回None
        """
        sql = """
        SELECT id, username, email, password_hash, created_at, updated_at
        FROM users
        WHERE username = %s
        """

        try:
            results = self.db.execute_query(sql, (username,))

            if results and len(results) > 0:
                user_data = results[0]
                return User(
                    user_id=user_data['id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    password_hash=user_data['password_hash'],
                    created_at=user_data['created_at'],
                    updated_at=user_data['updated_at']
                )

            return None

        except Exception as e:
            logger.error(f"获取用户 {username} 信息时发生错误: {e}")
            return None

    def _hash_password(self, password):   # finished
        """
        对密码进行哈希处理

        Args:
            password (str): 明文密码

        Returns:
            str: 哈希后的密码
        """
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    def _check_password(self, password, password_hash):   # finished
        """
        验证密码是否正确

        Args:
            password (str): 明文密码
            password_hash (str): 哈希密码

        Returns:
            bool: 密码正确返回True，否则返回False
        """
        return self._hash_password(password) == password_hash

class MySQLAuthService:  
    """MySQL用户认证服务类"""

    def __init__(self, secret_key=None):
        """
        初始化认证服务

        Args:
            secret_key (str, optional): JWT密钥，如果不提供则使用配置中的密钥
        """
        self.db = MySQLUserDB()
        self.secret_key = secret_key or JWT_SECRET_KEY

    def register(self, username, email, password):   # finished
        """
        用户注册

        Args:
            username (str): 用户名
            email (str): 邮箱
            password (str): 明文密码

        Returns:
            tuple: (成功标志, 消息)
        """
        # 验证密码长度
        if len(password) < 6:
            return False, "密码长度至少为6位"

        # 验证用户名格式
        if not username or len(username) < 3 or len(username) > 20:
            return False, "用户名长度必须在3-20个字符之间"

        # 验证邮箱格式
        if not email or '@' not in email:
            return False, "请输入有效的邮箱地址"

        # 检查用户名是否已存在
        if self.db.get_user_by_username(username):
            return False, "用户名已存在"

        # 创建用户
        if self.db.create_user(username, email, password):
            return True, "注册成功"
        else:
            return False, "注册失败，请稍后重试"

    def login(self, username, password):   # finished
        """
        用户登录

        Args:
            username (str): 用户名
            password (str): 明文密码

        Returns:
            tuple: (成功标志, 消息, token或None)
        """
        user = self.db.verify_user(username, password)
        if user:

            # 生成JWT token
            token = jwt.encode({
                'user_id': user.user_id,
                'username': user.username,
                'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
            }, self.secret_key, algorithm='HS256')

            return True, "登录成功", token
        else:
            return False, "用户名或密码错误", None

    def verify_token(self, token):   # finished
        """
        验证JWT令牌

        Args:
            token (str): JWT令牌

        Returns:
            dict or None: 解码后的用户信息，验证失败返回None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token已过期")
            return None
        except jwt.InvalidTokenError:
            logger.warning("无效的JWT token")
            return None

    def get_current_user(self, token):   # finished
        """
        根据token获取当前用户信息

        Args:
            token (str): JWT令牌

        Returns:
            User or None: 用户对象或None
        """
        payload = self.verify_token(token)
        if payload and 'user_id' in payload:
            return self.db.get_user_by_id(payload['user_id'])
        return None
