"""
AI电商宣传图生成器 - 主应用文件
整合所有模块，提供完整的Web服务
"""

from flask import Flask
from flask_cors import CORS
import os

# 导入配置
from config import MYSQL_CONFIG, JWT_SECRET_KEY

# 导入路由模块
from routes.auth_routes import auth_bp
from routes.image_routes import image_bp
from routes.history_routes import history_bp

def create_app():
    """
    创建Flask应用实例

    Returns:
        Flask: 配置完成的Flask应用实例
    """
    app = Flask(__name__)

    # 设置应用配置
    app.config['SECRET_KEY'] = JWT_SECRET_KEY
    app.config['MYSQL_CONFIG'] = MYSQL_CONFIG

    # 启用CORS
    CORS(app)

    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(image_bp, url_prefix='/image')
    app.register_blueprint(history_bp, url_prefix='/history')

    # 健康检查端点
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        健康检查端点

        GET /health

        Response:
            JSON: 应用健康状态信息
        """
        return {
            'status': 'healthy',
            'service': 'AI电商宣传图生成器',
            'version': '2.0.0',
            'modules': {
                'auth': 'loaded',
                'image': 'loaded',
                'history': 'loaded',
                'database': 'mysql',
                'ai_service': 'tongyi'
            }
        }

    # 根路径重定向
    @app.route('/', methods=['GET'])
    def index():
        """根路径"""
        return {
            'message': 'AI电商宣传图生成器 API',
            'version': '2.0.0',
            'docs': {
                'auth': '/auth',
                'image': '/image',
                'history': '/history',
                'health': '/health'
            }
        }

    return app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 AI电商宣传图生成器后端服务启动中...")
    print("📊 服务版本: 2.0.0")
    print("💾 数据库: MySQL")
    print("🤖 AI服务: 通义万相")
    print()
    print("📋 可用端点:")
    print("  🔐 认证相关:")
    print("    POST /auth/register        用户注册")
    print("    POST /auth/login          用户登录")
    print("    GET  /auth/profile        获取用户信息")
    print()
    print("  🖼️  图片生成:")
    print("    POST /image/generate      上传图片生成宣传图")
    print("    POST /image/generate-from-text  文字描述生成图片")
    print("    POST /image/simple-test   简单图片效果测试")
    print()
    print("  📚 历史记录:")
    print("    GET  /history/chat-history        获取会话列表")
    print("    GET  /history/chat-history/<id>   获取聊天历史")
    print("    DELETE /history/chat-history/<id> 删除聊天历史")
    print("    GET  /history/generation-records  获取生成记录")
    print()
    print("  🏥 系统状态:")
    print("    GET  /health              健康检查")
    print("    GET  /                    API信息")
    print()
    print("🌐 前端访问: http://localhost:8000")
    print("🔗 后端API: http://localhost:5000")
    print("=" * 60)

    # 启动服务
    app.run(
        debug=True,
        host='0.0.0.0',
        port=5000,
        use_reloader=True
    )
