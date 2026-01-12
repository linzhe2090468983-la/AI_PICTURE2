"""
数据库连接模块
提供MySQL数据库连接和基础操作功能
"""

import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from config import MYSQL_CONFIG
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """MySQL数据库连接管理类"""

    def __init__(self, config=None):
        """
        初始化数据库连接

        Args:
            config (dict, optional): 数据库配置，如果不提供则使用默认配置
        """
        self.config = config or MYSQL_CONFIG.copy()

    @contextmanager
    def get_connection(self):
        """
        获取数据库连接的上下文管理器

        Yields:
            connection: 数据库连接对象

        Raises:
            pymysql.Error: 数据库连接或操作错误
        """
        connection = None
        try:
            # 创建数据库连接
            connection = pymysql.connect(**self.config)
            logger.debug("数据库连接已建立")
            yield connection
        except pymysql.Error as e:
            logger.error(f"数据库连接错误: {e}")
            raise
        finally:
            if connection:
                connection.close()
                logger.debug("数据库连接已关闭")

    def execute_query(self, query, params=None, fetch=True):   # finished
        """
        执行SQL查询

        Args:
            query (str): SQL查询语句
            params (tuple or list, optional): 查询参数
            fetch (bool): 是否获取查询结果，默认为True

        Returns:
            list or int: 如果fetch=True返回查询结果列表，否则返回影响行数
        """
        with self.get_connection() as connection:

            # DictCursor: 返回字典类型的结果
            with connection.cursor(DictCursor) as cursor:
                try:
                    cursor.execute(query, params or ())
                    logger.debug(f"执行SQL: {query}")
                    if params:
                        logger.debug(f"参数: {params}")

                    if fetch:
                        result = cursor.fetchall()
                        logger.debug(f"查询到 {len(result)} 条记录")
                        return result
                    else:
                        connection.commit()
                        affected_rows = cursor.rowcount
                        logger.debug(f"影响了 {affected_rows} 行数据")
                        return affected_rows
                except pymysql.Error as e:
                    logger.error(f"SQL执行错误: {e}")
                    connection.rollback()
                    raise

    def create_tables(self):
        """
        创建必要的数据库表
        使用简单灵活的SQL语句，兼容老版本MySQL
        """
        tables_sql = [
            # 用户表
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_username (username),
                INDEX idx_email (email)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,

            # 聊天历史表
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                session_id VARCHAR(100) NOT NULL,
                message_type ENUM('user', 'system') NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_session (user_id, session_id),
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            # 图片模式聊天历史表
            """
            CREATE TABLE IF NOT EXISTS image_chat_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                session_id VARCHAR(100) NOT NULL,
                message_type ENUM('user', 'system') NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_session (user_id, session_id),
                INDEX idx_timestamp (timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,

            # 生成记录表
            """
            CREATE TABLE IF NOT EXISTS generation_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                image_url LONGTEXT NOT NULL,
                prompt TEXT,
                model VARCHAR(50),
                style VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_user_id (user_id),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        ]

        logger.info("开始创建数据库表...")
        for i, sql in enumerate(tables_sql, 1):
            try:
                self.execute_query(sql, fetch=False)
                logger.info(f"表 {i} 创建成功")
            except Exception as e:
                logger.error(f"创建表 {i} 失败: {e}")
                raise

        logger.info("所有数据库表创建完成")

    def test_connection(self):
        """
        测试数据库连接

        Returns:
            bool: 连接成功返回True，否则返回False
        """
        try:
            self.execute_query("SELECT 1 as test")
            logger.info("数据库连接测试成功")
            return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False

# 创建全局数据库连接实例
db_connection = DatabaseConnection()
