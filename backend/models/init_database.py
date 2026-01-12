#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建MySQL数据库和表结构
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import db_connection
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_database():
    """
    初始化数据库
    创建必要的表结构
    """
    try:
        logger.info("开始初始化数据库...")

        # 测试数据库连接
        logger.info("测试数据库连接...")
        if not db_connection.test_connection():
            logger.error("数据库连接失败，请检查配置")
            return False

        # 创建表结构
        logger.info("创建数据库表...")
        db_connection.create_tables()

        logger.info("✅ 数据库初始化完成！")
        return True

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False

def show_usage():
    """
    显示使用说明
    """
    print("""
MySQL数据库初始化脚本

使用前准备：
1. 安装MySQL服务器
2. 创建数据库用户和数据库
3. 配置环境变量或修改config.py中的MYSQL_CONFIG

环境变量配置：
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=your_username
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=ai_picture_gen

或者直接修改 backend/config.py 中的 MYSQL_CONFIG 配置

运行命令：
python init_database.py

注意：
- 确保MySQL服务正在运行
- 用户需要有创建表和插入数据的权限
- 数据库字符集将设置为utf8mb4以支持中文
""")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        show_usage()
    else:
        success = init_database()
        sys.exit(0 if success else 1)
