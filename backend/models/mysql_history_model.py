"""
MySQL历史记录模型模块
提供基于MySQL的用户生成记录和聊天历史的数据库操作
"""

import sys
import os

# 获取项目根目录
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 将项目根目录添加到 sys.path
sys.path.append(root_dir)

# 修改这一行 - 直接从根目录导入config而不是backend.config
from config import MYSQL_CONFIG
# 修改这一行 - 使用相对路径导入DatabaseConnection
from models.database import DatabaseConnection
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class MySQLHistoryDB:
    """MySQL历史数据存储类"""
    
    def __init__(self):
        """初始化历史数据数据库连接"""
        self.db = DatabaseConnection()
        self._create_tables_if_not_exists()
    
    def _create_tables_if_not_exists(self):
        """创建历史数据表（如果不存在）"""
        try:
            # 创建每日统计表
            daily_stats_table_sql = """
            CREATE TABLE IF NOT EXISTS daily_statistics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                total_users INT DEFAULT 0,
                total_generations INT DEFAULT 0,
                today_generations INT DEFAULT 0,
                most_popular_model VARCHAR(255),
                created_at DATETIME NOT NULL,
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            # 创建每周统计表
            weekly_stats_table_sql = """
            CREATE TABLE IF NOT EXISTS weekly_statistics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                weekly_trends JSON,
                model_stats JSON,
                user_ranking JSON,
                created_at DATETIME NOT NULL,
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            # 创建趋势统计表
            trend_stats_table_sql = """
            CREATE TABLE IF NOT EXISTS trend_statistics (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE NOT NULL,
                generation_count INT DEFAULT 0,
                user_growth INT DEFAULT 0,
                active_users INT DEFAULT 0,
                created_at DATETIME NOT NULL,
                UNIQUE KEY uk_date (date),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            self.db.execute_query(daily_stats_table_sql, fetch=False)
            self.db.execute_query(weekly_stats_table_sql, fetch=False)
            self.db.execute_query(trend_stats_table_sql, fetch=False)
            
            logger.info("历史数据表创建成功")
        except Exception as e:
            logger.error(f"创建历史数据表时出错: {str(e)}")
    
    def save_daily_statistics(self, stats_data):
        """保存每日统计数据"""
        try:
            sql = """
            INSERT INTO daily_statistics 
            (total_users, total_generations, today_generations, most_popular_model, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """
            self.db.execute_query(sql, (
                stats_data.get('total_users', 0),
                stats_data.get('total_generations', 0),
                stats_data.get('today_generations', 0),
                stats_data.get('most_popular_model', ''),
                stats_data.get('created_at')
            ), fetch=False)
            
            logger.info("每日统计数据保存成功")
        except Exception as e:
            logger.error(f"保存每日统计数据时出错: {str(e)}")
    
    def save_weekly_statistics(self, weekly_data):
        """保存每周统计数据"""
        try:
            sql = """
            INSERT INTO weekly_statistics 
            (weekly_trends, model_stats, user_ranking, created_at)
            VALUES (%s, %s, %s, %s)
            """
            self.db.execute_query(sql, (
                json.dumps(weekly_data.get('weekly_trends', []), ensure_ascii=False),
                json.dumps(weekly_data.get('model_stats', []), ensure_ascii=False),
                json.dumps(weekly_data.get('user_ranking', []), ensure_ascii=False),
                weekly_data.get('created_at')
            ), fetch=False)
            
            logger.info("每周统计数据保存成功")
        except Exception as e:
            logger.error(f"保存每周统计数据时出错: {str(e)}")
    
    def save_trend_statistics(self, date, generation_count=0, user_growth=0, active_users=0):
        """保存趋势统计数据"""
        try:
            sql = """
            INSERT INTO trend_statistics 
            (date, generation_count, user_growth, active_users, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            generation_count = VALUES(generation_count),
            user_growth = VALUES(user_growth),
            active_users = VALUES(active_users),
            created_at = VALUES(created_at)
            """
            self.db.execute_query(sql, (
                date,
                generation_count,
                user_growth,
                active_users,
                datetime.now()
            ), fetch=False)
            
            logger.info(f"趋势统计数据保存成功: {date}")
        except Exception as e:
            logger.error(f"保存趋势统计数据时出错: {str(e)}")
    
    def get_daily_statistics(self, days=30):
        """获取每日统计数据"""
        try:
            sql = """
            SELECT * FROM daily_statistics
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            ORDER BY created_at DESC
            """
            results = self.db.execute_query(sql, (days,))
            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'id': row['id'],
                    'total_users': row['total_users'],
                    'total_generations': row['total_generations'],
                    'today_generations': row['today_generations'],
                    'most_popular_model': row['most_popular_model'],
                    'created_at': row['created_at']
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"获取每日统计数据时出错: {str(e)}")
            return []
    
    def get_weekly_statistics(self, weeks=10):
        """获取每周统计数据"""
        try:
            sql = """
            SELECT * FROM weekly_statistics
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s WEEK)
            ORDER BY created_at DESC
            """
            results = self.db.execute_query(sql, (weeks,))
            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'id': row['id'],
                    'weekly_trends': json.loads(row['weekly_trends']) if row['weekly_trends'] else [],
                    'model_stats': json.loads(row['model_stats']) if row['model_stats'] else [],
                    'user_ranking': json.loads(row['user_ranking']) if row['user_ranking'] else [],
                    'created_at': row['created_at']
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"获取每周统计数据时出错: {str(e)}")
            return []
    
    def get_trend_statistics(self, days=90):
        """获取趋势统计数据"""
        try:
            sql = """
            SELECT * FROM trend_statistics
            WHERE date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
            ORDER BY date DESC
            """
            results = self.db.execute_query(sql, (days,))
            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'generation_count': row['generation_count'],
                    'user_growth': row['user_growth'],
                    'active_users': row['active_users'],
                    'created_at': row['created_at']
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"获取趋势统计数据时出错: {str(e)}")
            return []

    def save_generation_record(self, user_id, image_url, prompt=None, model=None, style=None, generation_type='image'):   # finished
        """
        保存生成记录

        Args:
            user_id (int): 用户ID
            image_url (str): 生成图片的URL
            prompt (str, optional): 提示词
            model (str, optional): 使用的模型
            style (str, optional): 生成的风格
            generation_type (str, optional): 生成类型 (image/text)

        Returns:
            bool: 成功返回True，失败返回False
        """
        sql = """
        INSERT INTO generation_records (user_id, image_url, prompt, model, style)
        VALUES (%s, %s, %s, %s, %s)
        """

        try:
            self.db.execute_query(sql, (user_id, image_url, prompt, model, style), fetch=False)
            logger.info(f"用户 {user_id} 的生成记录保存成功")
            return True
        except Exception as e:
            logger.error(f"保存用户 {user_id} 的生成记录失败: {e}")
            return False

    def get_user_generation_records(self, user_id, limit=50, offset=0):   # finished
        """
        获取用户生成记录

        Args:
            user_id (int): 用户ID
            limit (int): 返回记录数量限制，默认50
            offset (int): 偏移量，默认0

        Returns:
            list: 生成记录列表，每条记录包含所有字段
        """
        sql = """
        SELECT id, image_url, prompt, model, style, created_at
        FROM generation_records
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
        """

        try:
            results = self.db.execute_query(sql, (user_id, limit, offset))
            logger.info(f"获取用户 {user_id} 的 {len(results)} 条生成记录")
            return results
        except Exception as e:
            logger.error(f"获取用户 {user_id} 的生成记录失败: {e}")
            return []

    def get_generation_record_count(self, user_id):
        """
        获取用户生成记录总数

        Args:
            user_id (int): 用户ID

        Returns:
            int: 记录总数
        """
        sql = "SELECT COUNT(*) as count FROM generation_records WHERE user_id = %s"

        try:
            results = self.db.execute_query(sql, (user_id,))
            count = results[0]['count'] if results else 0
            logger.debug(f"用户 {user_id} 的生成记录总数: {count}")
            return count
        except Exception as e:
            logger.error(f"获取用户 {user_id} 的生成记录总数失败: {e}")
            return 0

    def save_chat_message(self, user_id, session_id, role, content, generation_type='text'):
        """保存聊天消息到数据库
        
        Args:
            user_id (int): 用户ID
            session_id (str): 会话ID
            role (str): 消息角色 (user/system)
            content (str): 消息内容
            generation_type (str): 生成类型 (text/image)，默认为text
        """
        try:
            # 使用数据库连接执行查询 - 现在使用chat_history表，与数据库创建脚本一致
            sql = """
            INSERT INTO chat_history (user_id, session_id, message_type, content)
            VALUES (%s, %s, %s, %s)
            """
            self.db.execute_query(sql, (user_id, session_id, role, content), fetch=False)
            
            print(f"✅ 聊天消息已保存到数据库: {content[:50]}...")
        except Exception as e:
            print(f"❌ 保存聊天消息失败: {e}")

    def get_recent_chat_messages(self, user_id, generation_type, limit=10):
        """获取最近的聊天消息
        
        Args:
            user_id (int): 用户ID
            generation_type (str): 生成类型 (text/image) - 这个参数现在被忽略，因为chat_history表不包含此字段
            limit (int): 限制返回的消息数量，默认为10
            
        Returns:
            list: 聊天消息列表
        """
        try:
            # 查询最近的聊天消息 - 现在使用chat_history表
            query = """
            SELECT id, user_id, session_id, message_type as role, content, timestamp
            FROM chat_history
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
            """
            results = self.db.execute_query(query, (user_id, limit))
            
            # 按时间倒序排列（最新的在最后）
            results.reverse()
            
            print(f"✅ 获取到 {len(results)} 条聊天消息")
            return results
        except Exception as e:
            print(f"❌ 获取聊天消息失败: {e}")
            return []

    def get_chat_history(self, user_id, session_id):   # finished
        """获取特定会话的聊天历史
        
        Args:
            user_id (int): 用户ID
            session_id (str): 会话ID
            
        Returns:
            list: 聊天历史记录列表
        """
        try:
            # 查询特定会话的聊天历史 - 使用chat_history表
            query = """
            SELECT id, user_id, session_id, message_type as role, content, timestamp
            FROM chat_history
            WHERE user_id = %s AND session_id = %s
            ORDER BY timestamp ASC
            """
            results = self.db.execute_query(query, (user_id, session_id))
            
            print(f"✅ 获取到会话 {session_id} 的 {len(results)} 条聊天记录")
            return results
        except Exception as e:
            print(f"❌ 获取聊天历史失败: {e}")
            return []

    def get_user_sessions(self, user_id):   # finished
        """
        获取用户的所有会话ID

        Args:
            user_id (int): 用户ID

        Returns:
            list: 会话ID列表，按最后消息时间倒序排列
        """
        sql = """
        SELECT DISTINCT session_id
        FROM chat_history
        WHERE user_id = %s
        ORDER BY MAX(timestamp) DESC
        """

        try:
            results = self.db.execute_query(sql, (user_id,))
            session_ids = [row['session_id'] for row in results]
            logger.info(f"获取用户 {user_id} 的 {len(session_ids)} 个会话")

            # ['session_001', 'session_002', 'session_003']
            return session_ids
        except Exception as e:
            logger.error(f"获取用户 {user_id} 的会话列表失败: {e}")
            return []

    def delete_chat_history(self, user_id, session_id):   # finished
        """
        删除特定会话的聊天历史

        Args:
            user_id (int): 用户ID
            session_id (str): 会话ID

        Returns:
            bool: 成功返回True，失败返回False
        """
        sql = "DELETE FROM chat_history WHERE user_id = %s AND session_id = %s"

        try:
            # fetch = Flase ：返回影响行数
            affected_rows = self.db.execute_query(sql, (user_id, session_id), fetch=False)
            logger.info(f"删除用户 {user_id} 会话 {session_id} 的 {affected_rows} 条聊天记录")
            return True
        except Exception as e:
            logger.error(f"删除用户 {user_id} 会话 {session_id} 的聊天记录失败: {e}")
            return False

    def cleanup_old_records(self, days_old=90):   # finished
        """
        清理旧的记录（可选功能）

        Args:
            days_old (int): 删除多少天前的记录，默认90天

        Returns:
            tuple: (删除的聊天记录数, 删除的生成记录数)
        """
        try:
            # 删除旧的聊天记录
            chat_sql = f"""
            DELETE FROM chat_history
            WHERE timestamp < DATE_SUB(NOW(), INTERVAL {days_old} DAY)
            """
            chat_deleted = self.db.execute_query(chat_sql, fetch=False)

            # 删除旧的生成记录
            gen_sql = f"""
            DELETE FROM generation_records
            WHERE created_at < DATE_SUB(NOW(), INTERVAL {days_old} DAY)
            """
            gen_deleted = self.db.execute_query(gen_sql, fetch=False)

            logger.info(f"清理了 {chat_deleted} 条聊天记录和 {gen_deleted} 条生成记录")
            return chat_deleted, gen_deleted

        except Exception as e:
            logger.error(f"清理旧记录失败: {e}")
            return 0, 0

    def save_image_chat_message(self, user_id, session_id, role, content):
        """保存图片模式聊天消息到数据库
        
        Args:
            user_id (int): 用户ID
            session_id (str): 会话ID
            role (str): 消息角色 (user/system)
            content (str): 消息内容
        """
        try:
            # 使用数据库连接执行查询 - 使用image_chat_history表
            sql = """
            INSERT INTO image_chat_history (user_id, session_id, message_type, content)
            VALUES (%s, %s, %s, %s)
            """
            self.db.execute_query(sql, (user_id, session_id, role, content), fetch=False)
            
            print(f"✅ 图片模式聊天消息已保存到数据库: {content[:50]}...")
        except Exception as e:
            print(f"❌ 保存图片模式聊天消息失败: {e}")

    def get_recent_image_chat_messages(self, user_id, limit=10):
        """获取最近的图片模式聊天消息
        
        Args:
            user_id (int): 用户ID
            limit (int): 限制返回的消息数量，默认为10
            
        Returns:
            list: 聊天消息列表
        """
        try:
            # 查询最近的图片模式聊天消息 - 使用image_chat_history表
            query = """
            SELECT id, user_id, session_id, message_type as role, content, timestamp
            FROM image_chat_history
            WHERE user_id = %s
            ORDER BY timestamp DESC
            LIMIT %s
            """
            results = self.db.execute_query(query, (user_id, limit))
            
            # 按时间倒序排列（最新的在最后）
            results.reverse()
            
            print(f"✅ 获取到 {len(results)} 条图片模式聊天消息")
            return results
        except Exception as e:
            print(f"❌ 获取图片模式聊天消息失败: {e}")
            return []
