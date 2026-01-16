import logging
import threading
from datetime import datetime
import sys
import os

# 获取项目根目录并添加到系统路径
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# 添加导入
try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    print("警告: 未找到 schedule 库，请运行 'pip install schedule' 安装")

import time
from backend.data_analysis import DataAnalysisService
from backend.models.mysql_history_model import MySQLHistoryDB

logger = logging.getLogger(__name__)

class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self):
        """初始化调度器"""
        self.analysis_service = DataAnalysisService()
        self.history_db = MySQLHistoryDB()
        self.running = False
        
    def daily_statistics_job(self):
        """每日统计任务"""
        try:
            logger.info("开始执行每日统计任务")
            
            # 获取当前日期的基础统计数据
            stats = self.analysis_service.get_basic_statistics()
            
            # 添加时间戳
            stats['created_at'] = datetime.now()
            
            # 存储到历史数据库
            self.history_db.save_daily_statistics(stats)
            
            logger.info("每日统计任务完成")
        except Exception as e:
            logger.error(f"执行每日统计任务时出错: {str(e)}")
    
    def weekly_statistics_job(self):
        """每周统计任务"""
        try:
            logger.info("开始执行每周统计任务")
            
            # 获取周趋势数据
            weekly_trends = self.analysis_service.get_daily_generation_trends(days=7)
            
            # 获取模型使用情况
            model_stats = self.analysis_service.get_model_usage_statistics()
            
            # 获取用户排名
            user_ranking = self.analysis_service.get_user_generation_ranking(limit=10)
            
            # 存储周统计数据
            weekly_data = {
                'weekly_trends': weekly_trends,
                'model_stats': model_stats,
                'user_ranking': user_ranking,
                'created_at': datetime.now()
            }
            
            self.history_db.save_weekly_statistics(weekly_data)
            
            logger.info("每周统计任务完成")
        except Exception as e:
            logger.error(f"执行每周统计任务时出错: {str(e)}")
    
    def setup_schedule(self):
        """设置定时任务"""
        if not SCHEDULE_AVAILABLE:
            logger.error("无法设置定时任务: schedule 库未安装")
            print("错误: 请先安装 schedule 库，运行 'pip install schedule'")
            return
            
        # 每天凌晨2点执行每日统计
        schedule.every().day.at("02:00").do(self.daily_statistics_job)
        
        # 每周一凌晨3点执行周统计
        schedule.every().monday.at("03:00").do(self.weekly_statistics_job)
        
        logger.info("定时任务已设置")
    
    def run_scheduler(self):
        """运行调度器"""
        self.setup_schedule()
        self.running = True
        
        if not SCHEDULE_AVAILABLE:
            logger.error("调度器无法运行: schedule 库未安装")
            return
            
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    
    def start(self):
        """启动调度器（在新线程中运行）"""
        if not SCHEDULE_AVAILABLE:
            logger.error("调度器无法启动: schedule 库未安装")
            return
            
        scheduler_thread = threading.Thread(target=self.run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        logger.info("定时任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        logger.info("定时任务调度器已停止")

# 全局调度器实例
scheduler = TaskScheduler()

def start_scheduler():
    """启动定时任务调度器"""
    scheduler.start()

def stop_scheduler():
    """停止定时任务调度器"""
    scheduler.stop()

if __name__ == "__main__":
    # 启动调度器并保持运行
    start_scheduler()
    
    # 保持主线程运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_scheduler()
        print("调度器已关闭")
