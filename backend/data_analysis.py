import sys
import os

# 获取项目根目录
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 将项目根目录添加到 sys.path
sys.path.append(root_dir)

from backend.config import MYSQL_CONFIG
from backend.models.database import DatabaseConnection
from backend.models.mysql_history_model import MySQLHistoryDB
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

logger = logging.getLogger(__name__)

class DataAnalysisService:
    """数据统计分析服务类"""
    
    def __init__(self):
        """初始化数据统计服务"""
        self.db = DatabaseConnection()
        self.history_db = MySQLHistoryDB()
    
    def get_basic_statistics(self) -> Dict[str, Any]:
        """获取基础统计数据"""
        try:
            # 使用数据库服务中的execute_query方法替代直接的游标操作
            total_users_sql = "SELECT COUNT(*) as count FROM users"
            total_users_result = self.db.execute_query(total_users_sql)
            total_users = total_users_result[0]['count'] if total_users_result else 0
            
            total_generations_sql = "SELECT COUNT(*) as count FROM generation_records"
            total_generations_result = self.db.execute_query(total_generations_sql)
            total_generations = total_generations_result[0]['count'] if total_generations_result else 0
            
            today = datetime.now().date()
            today_generations_sql = "SELECT COUNT(*) as count FROM generation_records WHERE DATE(created_at) = %s"
            today_generations_result = self.db.execute_query(today_generations_sql, (today,))
            today_generations = today_generations_result[0]['count'] if today_generations_result else 0
            
            # 修复查询，使用正确的列名
            most_popular_model_sql = """
                SELECT model, COUNT(*) as count 
                FROM generation_records 
                WHERE model IS NOT NULL
                GROUP BY model 
                ORDER BY count DESC 
                LIMIT 1
            """
            most_popular_model_result = self.db.execute_query(most_popular_model_sql)
            popular_model = most_popular_model_result[0]['model'] if most_popular_model_result and most_popular_model_result[0]['model'] else "无"
            
            return {
                "total_users": total_users,
                "total_generations": total_generations,
                "today_generations": today_generations,
                "most_popular_model": popular_model
            }
        except Exception as e:
            logger.error(f"获取基础统计数据时出错: {str(e)}")
            return {}
    
    def get_daily_generation_trends(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取每日生成趋势"""
        try:
            # 使用execute_query方法
            sql = """
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM generation_records
                WHERE created_at >= %s
                GROUP BY DATE(created_at)
                ORDER BY date
            """
            start_date = datetime.now() - timedelta(days=days)
            results = self.db.execute_query(sql, (start_date,))
            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "date": str(row['date']),
                    "count": row['count']
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"获取每日生成趋势时出错: {str(e)}")
            return []
    
    def get_model_usage_statistics(self) -> List[Dict[str, Any]]:
        """获取各模型使用统计"""
        try:
            sql = """
                SELECT model, COUNT(*) as count
                FROM generation_records
                WHERE model IS NOT NULL
                GROUP BY model
                ORDER BY count DESC
            """
            results = self.db.execute_query(sql)
            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "model": row['model'],
                    "usage_count": row['count']
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"获取模型使用统计时出错: {str(e)}")
            return []
    
    def get_user_generation_ranking(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取用户生成排行榜"""
        try:
            sql = """
                SELECT u.username, COUNT(g.id) as generation_count
                FROM users u
                JOIN generation_records g ON u.id = g.user_id
                GROUP BY u.id, u.username
                ORDER BY generation_count DESC
                LIMIT %s
            """
            results = self.db.execute_query(sql, (limit,))
            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "username": row['username'],
                    "generation_count": row['generation_count']
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"获取用户生成排行榜时出错: {str(e)}")
            return []
    
    def get_style_preferences(self) -> List[Dict[str, Any]]:
        """获取风格偏好统计"""
        try:
            sql = """
                SELECT style, COUNT(*) as count
                FROM generation_records
                WHERE style IS NOT NULL
                GROUP BY style
                ORDER BY count DESC
            """
            results = self.db.execute_query(sql)
            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "style": row['style'],
                    "usage_count": row['count']
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"获取风格偏好统计时出错: {str(e)}")
            return []
    
    def get_generation_time_analysis(self) -> Dict[str, Any]:
        """获取生成时间分析（按小时分布）"""
        try:
            sql = """
                SELECT HOUR(created_at) as hour, COUNT(*) as count
                FROM generation_records
                GROUP BY HOUR(created_at)
                ORDER BY hour
            """
            results = self.db.execute_query(sql)
            
            hourly_distribution = {}
            for row in results:
                hourly_distribution[int(row['hour'])] = row['count']
            
            # 补全24小时的数据
            full_distribution = {}
            for hour in range(24):
                full_distribution[hour] = hourly_distribution.get(hour, 0)
            
            return {
                "hourly_distribution": full_distribution
            }
        except Exception as e:
            logger.error(f"获取生成时间分析时出错: {str(e)}")
            return {}
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近活动记录"""
        try:
            sql = """
                SELECT u.username, g.prompt, g.model, g.style, g.created_at
                FROM generation_records g
                JOIN users u ON g.user_id = u.id
                ORDER BY g.created_at DESC
                LIMIT %s
            """
            results = self.db.execute_query(sql, (limit,))
            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "username": row['username'],
                    "prompt": row['prompt'],
                    "model_used": row['model'],
                    "style_used": row['style'],
                    "created_at": str(row['created_at'])
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"获取最近活动记录时出错: {str(e)}")
            return []
    
    def get_user_growth_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取用户增长趋势"""
        try:
            sql = """
                SELECT DATE(created_at) as date, COUNT(*) as new_users
                FROM users
                WHERE created_at >= %s
                GROUP BY DATE(created_at)
                ORDER BY date
            """
            start_date = datetime.now() - timedelta(days=days)
            results = self.db.execute_query(sql, (start_date,))
            
            formatted_results = []
            for row in results:
                formatted_results.append({
                    "date": str(row['date']),
                    "new_users": row['new_users']
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"获取用户增长趋势时出错: {str(e)}")
            return []
    
    def get_text_vs_image_generation_ratio(self) -> Dict[str, int]:
        """获取文本生成与图片生成的比例"""
        try:
            # 获取文本生成数量（来自chat_history表）
            text_sql = "SELECT COUNT(*) as text_generations FROM chat_history"
            text_result = self.db.execute_query(text_sql)
            text_generations = text_result[0]['text_generations'] or 0
            
            # 获取图片生成数量（来自generation_records表）
            image_sql = "SELECT COUNT(*) as image_generations FROM generation_records"
            image_result = self.db.execute_query(image_sql)
            image_generations = image_result[0]['image_generations'] or 0
            
            # 计算总数
            total_generations = text_generations + image_generations
            
            # 计算比例
            text_ratio = round(text_generations / total_generations * 100, 2) if total_generations > 0 else 0
            image_ratio = round(image_generations / total_generations * 100, 2) if total_generations > 0 else 0
            
            return {
                "text_generations": text_generations,
                "image_generations": image_generations,
                "text_ratio": text_ratio,
                "image_ratio": image_ratio
            }
        except Exception as e:
            logger.error(f"获取文本与图片生成比例时出错: {str(e)}")
            return {"text_generations": 0, "image_generations": 0, "text_ratio": 0, "image_ratio": 0}

    def get_active_users_count(self, days: int = 1) -> int:
        """获取指定天数内的活跃用户数"""
        try:
            sql = """
                SELECT COUNT(DISTINCT user_id) as active_users
                FROM generation_records
                WHERE created_at >= %s
            """
            start_date = datetime.now() - timedelta(days=days)
            result = self.db.execute_query(sql, (start_date,))
            return result[0]['active_users'] if result else 0
        except Exception as e:
            logger.error(f"获取活跃用户数时出错: {str(e)}")
            return 0

    def calculate_growth_rate(self, current_value: int, previous_value: int) -> float:
        """计算增长率"""
        if previous_value == 0:
            return 100.0 if current_value > 0 else 0.0
        return round(((current_value - previous_value) / previous_value) * 100, 2)

    def get_growth_statistics(self) -> Dict[str, Any]:
        """获取增长统计数据"""
        try:
            # 获取今天的统计
            today_total_sql = "SELECT COUNT(*) as count FROM generation_records WHERE DATE(created_at) = CURDATE()"
            today_result = self.db.execute_query(today_total_sql)
            today_total = today_result[0]['count'] if today_result else 0
            
            # 获取昨天的统计
            yesterday_total_sql = "SELECT COUNT(*) as count FROM generation_records WHERE DATE(created_at) = DATE_SUB(CURDATE(), 1)"
            yesterday_result = self.db.execute_query(yesterday_total_sql)
            yesterday_total = yesterday_result[0]['count'] if yesterday_result else 0
            
            # 计算增长率
            generation_growth_rate = self.calculate_growth_rate(today_total, yesterday_total)
            
            # 获取本周的统计
            week_start = datetime.now() - timedelta(days=datetime.now().weekday())
            this_week_sql = "SELECT COUNT(*) as count FROM generation_records WHERE created_at >= %s"
            this_week_result = self.db.execute_query(this_week_sql, (week_start,))
            this_week_total = this_week_result[0]['count'] if this_week_result else 0
            
            # 获取上周的统计
            last_week_start = week_start - timedelta(weeks=1)
            last_week_end = week_start - timedelta(days=1)
            last_week_sql = "SELECT COUNT(*) as count FROM generation_records WHERE created_at >= %s AND created_at <= %s"
            last_week_result = self.db.execute_query(last_week_sql, (last_week_start, last_week_end))
            last_week_total = last_week_result[0]['count'] if last_week_result else 0
            
            week_growth_rate = self.calculate_growth_rate(this_week_total, last_week_total)
            
            # 获取活跃用户增长
            today_active = self.get_active_users_count(1)
            yesterday_active = self.get_active_users_count(2) - self.get_active_users_count(1)
            active_user_growth_rate = self.calculate_growth_rate(today_active, yesterday_active)
            
            return {
                "today_generation_growth_rate": generation_growth_rate,
                "this_week_generation_growth_rate": week_growth_rate,
                "today_active_user_growth_rate": active_user_growth_rate,
                "today_total": today_total,
                "yesterday_total": yesterday_total,
                "this_week_total": this_week_total,
                "last_week_total": last_week_total,
                "today_active_users": today_active,
                "yesterday_active_users": yesterday_active
            }
        except Exception as e:
            logger.error(f"获取增长统计数据时出错: {str(e)}")
            return {}

    def save_current_day_trend(self):
        """保存当天的趋势数据到历史表"""
        try:
            # 获取今天的生成数量
            today_gen_sql = "SELECT COUNT(*) as count FROM generation_records WHERE DATE(created_at) = CURDATE()"
            today_gen_result = self.db.execute_query(today_gen_sql)
            today_generation_count = today_gen_result[0]['count'] if today_gen_result else 0
            
            # 获取今天的新增用户数
            today_user_sql = "SELECT COUNT(*) as count FROM users WHERE DATE(created_at) = CURDATE()"
            today_user_result = self.db.execute_query(today_user_sql)
            today_user_growth = today_user_result[0]['count'] if today_user_result else 0
            
            # 获取今天的活跃用户数
            today_active_users = self.get_active_users_count(1)
            
            # 保存到趋势统计表
            from datetime import date
            self.history_db.save_trend_statistics(
                date=date.today(),
                generation_count=today_generation_count,
                user_growth=today_user_growth,
                active_users=today_active_users
            )
            
            logger.info("当天趋势数据保存成功")
        except Exception as e:
            logger.error(f"保存当天趋势数据时出错: {str(e)}")

    def get_statistics_for_date(self, target_date: str) -> Dict[str, Any]:
        """获取指定日期的详细统计信息"""
        try:
            # 解析输入的日期字符串
            from datetime import datetime
            parsed_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            
            # 查询当天的用户注册数
            user_sql = "SELECT COUNT(*) as count FROM users WHERE DATE(created_at) = %s"
            user_result = self.db.execute_query(user_sql, (parsed_date,))
            new_users = user_result[0]['count'] if user_result else 0
            
            # 查询当天的生成记录数
            gen_sql = "SELECT COUNT(*) as count FROM generation_records WHERE DATE(created_at) = %s"
            gen_result = self.db.execute_query(gen_sql, (parsed_date,))
            generation_count = gen_result[0]['count'] if gen_result else 0
            
            # 查询当天最热门的模型
            model_sql = """
                SELECT model, COUNT(*) as count 
                FROM generation_records 
                WHERE DATE(created_at) = %s AND model IS NOT NULL
                GROUP BY model 
                ORDER BY count DESC 
                LIMIT 1
            """
            model_result = self.db.execute_query(model_sql, (parsed_date,))
            most_popular_model = model_result[0]['model'] if model_result and model_result[0]['model'] else "无"
            
            # 查询当天最流行的风格
            style_sql = """
                SELECT style, COUNT(*) as count 
                FROM generation_records 
                WHERE DATE(created_at) = %s AND style IS NOT NULL
                GROUP BY style 
                ORDER BY count DESC 
                LIMIT 1
            """
            style_result = self.db.execute_query(style_sql, (parsed_date,))
            most_popular_style = style_result[0]['style'] if style_result and style_result[0]['style'] else "无"
            
            # 查询当天的活跃用户数
            active_users_sql = """
                SELECT COUNT(DISTINCT user_id) as count
                FROM generation_records
                WHERE DATE(created_at) = %s
            """
            active_users_result = self.db.execute_query(active_users_sql, (parsed_date,))
            active_users = active_users_result[0]['count'] if active_users_result else 0
            
            # 查询当天的风格偏好统计
            style_preference_sql = """
                SELECT style, COUNT(*) as count
                FROM generation_records
                WHERE DATE(created_at) = %s AND style IS NOT NULL
                GROUP BY style
                ORDER BY count DESC
            """
            style_preference_result = self.db.execute_query(style_preference_sql, (parsed_date,))
            style_preferences = [{"style": row['style'], "usage_count": row['count']} for row in style_preference_result]
            
            # 查询当天的模型使用统计
            model_usage_sql = """
                SELECT model, COUNT(*) as count
                FROM generation_records
                WHERE DATE(created_at) = %s AND model IS NOT NULL
                GROUP BY model
                ORDER BY count DESC
            """
            model_usage_result = self.db.execute_query(model_usage_sql, (parsed_date,))
            model_usage = [{"model": row['model'], "usage_count": row['count']} for row in model_usage_result]
            
            # 查询当天的每小时生成趋势
            hourly_trend_sql = """
                SELECT HOUR(created_at) as hour, COUNT(*) as count
                FROM generation_records
                WHERE DATE(created_at) = %s
                GROUP BY HOUR(created_at)
                ORDER BY hour
            """
            hourly_trend_result = self.db.execute_query(hourly_trend_sql, (parsed_date,))
            hourly_trends = {int(row['hour']): row['count'] for row in hourly_trend_result}
            
            # 补全24小时的数据
            full_hourly_trends = {}
            for hour in range(24):
                full_hourly_trends[hour] = hourly_trends.get(hour, 0)
            
            return {
                "date": str(parsed_date),
                "new_users": new_users,
                "generation_count": generation_count,
                "active_users": active_users,
                "most_popular_model": most_popular_model,
                "most_popular_style": most_popular_style,
                "style_preferences": style_preferences,
                "model_usage": model_usage,
                "hourly_trends": full_hourly_trends
            }
        except ValueError:
            logger.error(f"日期格式错误: {target_date}，请使用 YYYY-MM-DD 格式")
            return {}
        except Exception as e:
            logger.error(f"获取指定日期统计信息时出错: {str(e)}")
            return {}

def main():
    """主函数，用于演示和测试数据统计分析功能"""
    service = DataAnalysisService()
    
    while True:
        print("\n=== 数据统计分析系统 ===")
        print("1. 查看指定日期统计信息")
        print("2. 查看默认统计信息")
        print("3. 退出程序")
        print("请选择操作 (输入数字 1-3):")
        
        choice = input().strip()
        
        if choice == '1':
            print("\n请输入要查询的日期 (格式: YYYY-MM-DD):")
            user_input = input().strip()
            
            try:
                # 尝试解析用户输入的日期
                from datetime import datetime
                parsed_date = datetime.strptime(user_input, '%Y-%m-%d')
                print(f"\n正在查询 {user_input} 的详细统计信息...")
                
                # 获取指定日期的统计信息
                date_stats = service.get_statistics_for_date(user_input)
                if date_stats:
                    print(f"\n=== {date_stats['date']} 详细统计信息 ===")
                    print(f"新增用户数: {date_stats['new_users']}")
                    print(f"生成次数: {date_stats['generation_count']}")
                    print(f"活跃用户数: {date_stats['active_users']}")
                    print(f"最受欢迎的模型: {date_stats['most_popular_model']}")
                    print(f"最受欢迎的风格: {date_stats['most_popular_style']}")
                    
                    print("\n风格偏好统计:")
                    for pref in date_stats['style_preferences'][:5]:  # 显示前5个
                        print(f"  {pref['style']}: {pref['usage_count']}次")
                    
                    print("\n模型使用统计:")
                    for usage in date_stats['model_usage'][:5]:  # 显示前5个
                        print(f"  {usage['model']}: {usage['usage_count']}次")
                    
                    print("\n每小时生成趋势:")
                    hourly_trends = date_stats['hourly_trends']
                    for hour in sorted(hourly_trends.keys()):
                        if hourly_trends[hour] > 0:  # 只显示有数据的小时
                            print(f"  {hour:02d}:00 - {hourly_trends[hour]}次")
                else:
                    print(f"未能获取 {user_input} 的统计信息，请确认日期格式正确且数据存在。")
            except ValueError:
                print(f"日期格式错误: {user_input}，请使用 YYYY-MM-DD 格式")
        
        elif choice == '2':
            print("\n=== 基础统计数据 ===")
            basic_stats = service.get_basic_statistics()
            print(f"总用户数: {basic_stats.get('total_users', 0)}")
            print(f"总生成次数: {basic_stats.get('total_generations', 0)}")
            print(f"今日生成次数: {basic_stats.get('today_generations', 0)}")
            print(f"最受欢迎的模型: {basic_stats.get('most_popular_model', '无')}")

            print("\n=== 增长统计数据 ===")
            growth_stats = service.get_growth_statistics()
            print(f"今日生成量增长率: {growth_stats.get('today_generation_growth_rate', 0)}%")
            print(f"本周生成量增长率: {growth_stats.get('this_week_generation_growth_rate', 0)}%")
            print(f"今日活跃用户增长率: {growth_stats.get('today_active_user_growth_rate', 0)}%")

            print("\n=== 每日生成趋势 (最近7天) ===")
            trends = service.get_daily_generation_trends()
            for trend in trends:
                print(f"{trend['date']}: {trend['count']}次")

            print("\n=== 模型使用统计 ===")
            model_stats = service.get_model_usage_statistics()
            for stat in model_stats[:5]:  # 显示前5个
                print(f"{stat['model']}: {stat['usage_count']}次")

            print("\n=== 用户生成排行榜 (前10) ===")
            user_ranking = service.get_user_generation_ranking()
            for i, user in enumerate(user_ranking, 1):
                print(f"{i}. {user['username']}: {user['generation_count']}次")

            print("\n=== 风格偏好统计 ===")
            style_prefs = service.get_style_preferences()
            for pref in style_prefs[:5]:  # 显示前5个
                print(f"{pref['style']}: {pref['usage_count']}次")

            print("\n=== 生成时间分析 (按小时) ===")
            time_analysis = service.get_generation_time_analysis()
            hourly_dist = time_analysis.get('hourly_distribution', {})
            peak_hour = max(hourly_dist, key=hourly_dist.get) if hourly_dist else None
            print(f"最活跃时段: {peak_hour}点 (如果可用)")

            print("\n=== 最近活动记录 ===")
            recent_activity = service.get_recent_activity()
            for activity in recent_activity:
                print(f"{activity['created_at']} - {activity['username']}: "
                      f"使用{activity['model_used']}模型, 风格{activity['style_used']}")

            print("\n=== 用户增长趋势 (最近30天) ===")
            growth_trend = service.get_user_growth_trend()
            for trend in growth_trend[-5:]:  # 显示最近5天
                print(f"{trend['date']}: 新增{trend['new_users']}用户")

            print("\n=== 文本与图片生成比例 ===")
            ratio = service.get_text_vs_image_generation_ratio()
            print(f"文本生成: {ratio.get('text_generations', 0)} ({ratio.get('text_ratio', 0)}%)")
            print(f"图片生成: {ratio.get('image_generations', 0)} ({ratio.get('image_ratio', 0)}%)")

        elif choice == '3':
            print("感谢使用，再见！")
            break
        
        else:
            print("无效的选择，请输入 1、2 或 3")


if __name__ == "__main__":
    main()