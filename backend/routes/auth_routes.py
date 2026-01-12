"""
认证路由模块
处理用户注册、登录、个人资料等认证相关请求
"""

from flask import Blueprint, request, jsonify
from models.mysql_user_model import MySQLAuthService

# 创建认证蓝图,auth_bp.route 是 Flask 中用于在蓝本（Blueprint）上定义路由的装饰器，它让路由可以模块化管理并在注册时自动添加统一前缀。
auth_bp = Blueprint('auth', __name__)

# 初始化认证服务
auth_service = MySQLAuthService()

@auth_bp.route('/register', methods=['POST'])   # finished
def register():
    """
    用户注册端点

    POST /auth/register
    Content-Type: application/json

    Request Body:
    {
        "username": "用户名",
        "email": "邮箱",
        "password": "密码"
    }

    Response:
    {
        "success": true/false,
        "message": "注册结果信息"
    }
    """
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400

        success, message = auth_service.register(username, email, password)
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])   # finished
def login():
    """
    用户登录端点

    POST /auth/login
    Content-Type: application/json

    Request Body:
    {
        "username": "用户名",
        "password": "密码"
    }

    Response:
    {
        "success": true/false,
        "message": "登录结果信息",
        "token": "JWT令牌" (成功时返回),
        "user": {
            "user_id": 1,
            "username": "用户名"
        } (成功时返回)
    }
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400

        success, message, token = auth_service.login(username, password)
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'token': token,
                'user': {
                    'user_id': auth_service.get_current_user(token).user_id,
                    'username': username
                }
            })
        else:
            return jsonify({'success': False, 'message': message}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['GET'])   # finished
def profile():
    """
    获取用户信息端点

    GET /auth/profile
    Authorization: Bearer <token>

    Response:
    {
        "success": true,
        "user": {
            "user_id": 1,
            "username": "用户名"
        }
    }
    """
    try:
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'success': False, 'message': '缺少认证令牌'}), 401

        # 去掉 "Bearer " 前缀
        if token.startswith('Bearer '):
            token = token[7:]

        user_info = auth_service.verify_token(token)
        if user_info:
            return jsonify({
                'success': True,
                'user': {
                    'user_id': user_info['user_id'],
                    'username': user_info['username']
                }
            })
        else:
            return jsonify({'success': False, 'message': '认证失败'}), 401
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取用户信息失败: {str(e)}'}), 500
