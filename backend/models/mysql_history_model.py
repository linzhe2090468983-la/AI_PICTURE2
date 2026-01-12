"""
MySQL历史记录模型模块
提供基于MySQL的用户生成记录和聊天历史的数据库操作
"""

from models.database import db_connection
import logging

logger = logging.getLogger(__name__)

class MySQLHistoryDB:
    """MySQL历史记录数据库操作类"""

    def __init__(self):
        """
        初始化数据库连接
        使用全局数据库连接实例
        """
        self.db = db_connection

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
