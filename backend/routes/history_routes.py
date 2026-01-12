"""
历史记录路由模块
处理聊天历史和生成记录的查询和管理
"""

from flask import Blueprint, request, jsonify
from models.mysql_user_model import MySQLAuthService
from models.mysql_history_model import MySQLHistoryDB

# 创建历史记录蓝图
history_bp = Blueprint('history', __name__)

# 初始化服务
auth_service = MySQLAuthService()
history_db = MySQLHistoryDB()

@history_bp.route('/chat-history', methods=['GET'])   # finished
def get_all_sessions():
    """
    获取用户的所有会话ID列表

    GET /history/chat-history

    # 'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
    Authorization: Bearer <token>

    Response:
    {
        "sessions": ["session_id_1", "session_id_2"],
        "total_sessions": 2
    }
    """
    try:
        # 检查认证令牌
        token = request.headers.get('Authorization')
        user_info = None
        if token and token.startswith('Bearer '):
            token = token[7:]
            user_info = auth_service.verify_token(token)

        if not user_info:
            return jsonify({'error': '认证失败'}), 401

        sessions = history_db.get_user_sessions(user_info['user_id'])

        return jsonify({
            'sessions': sessions,
            'total_sessions': len(sessions)
        })

    except Exception as e:
        return jsonify({'error': f'获取会话列表失败: {str(e)}'}), 500

@history_bp.route('/chat-history/<session_id>', methods=['GET'])   # finished
def get_chat_history(session_id):
    """
    获取特定会话的聊天历史

    GET /history/chat-history/{session_id}
    Authorization: Bearer <token>

    Response:
    {
        "session_id": "session_id",
        "history": [
            {
                "id": 1,
                "message_type": "user",
                "content": "消息内容",
                "timestamp": "2025-01-01 12:00:00"
            }
        ],
        "total_messages": 1
    }
    """
    try:
        # 检查认证令牌
        token = request.headers.get('Authorization')
        user_info = None
        if token and token.startswith('Bearer '):
            token = token[7:]
            user_info = auth_service.verify_token(token)

        if not user_info:
            return jsonify({'error': '认证失败'}), 401

        chat_records = history_db.get_chat_history(user_info['user_id'], session_id)

        return jsonify({
            'session_id': session_id,
            'history': chat_records,
            'total_messages': len(chat_records)
        })

    except Exception as e:
        return jsonify({'error': f'获取聊天历史失败: {str(e)}'}), 500

@history_bp.route('/chat-history/<session_id>', methods=['DELETE'])   # finished
def delete_chat_history(session_id):
    """
    删除特定会话的聊天历史

    DELETE /history/chat-history/{session_id}
    Authorization: Bearer <token>

    Response:
    {
        "success": true,
        "message": "会话历史已清除"
    }
    """
    try:
        # 检查认证令牌
        token = request.headers.get('Authorization')
        user_info = None
        if token and token.startswith('Bearer '):
            token = token[7:]
            user_info = auth_service.verify_token(token)

        if not user_info:
            return jsonify({'error': '认证失败'}), 401

        success = history_db.delete_chat_history(user_info['user_id'], session_id)

        if success:
            return jsonify({'success': True, 'message': '会话历史已清除'})
        else:
            return jsonify({'error': '删除失败'}), 500

    except Exception as e:
        return jsonify({'error': f'删除聊天历史失败: {str(e)}'}), 500

@history_bp.route('/generation-records', methods=['GET'])   # finished
def get_user_generation_records():
    """
    获取用户的生成记录

    GET /history/generation-records?limit=50&offset=0
    Authorization: Bearer <token>

    Query Parameters:
    - limit: 返回记录数量限制 (默认50)
    - offset: 偏移量 (默认0)

    Response:
    {
        "records": [
            {
                "id": 1,
                "image_url": "图片URL",
                "prompt": "提示词",
                "model": "模型",
                "style": "风格",
                "created_at": "2025-01-01 12:00:00"
            }
        ],
        "total": 1,
        "limit": 50,
        "offset": 0
    }
    """
    try:
        # 检查认证令牌
        token = request.headers.get('Authorization')
        user_info = None
        if token and token.startswith('Bearer '):
            token = token[7:]
            user_info = auth_service.verify_token(token)

        if not user_info:
            return jsonify({'error': '认证失败'}), 401

        # 获取查询参数
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        # 限制查询数量
        limit = min(limit, 100)  # 最多返回100条记录

        records = history_db.get_user_generation_records(user_info['user_id'], limit, offset)

        return jsonify({
            'records': records,
            'total': len(records),
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        return jsonify({'error': f'获取生成记录失败: {str(e)}'}), 500

@history_bp.route('/recent-chat-messages', methods=['GET'])   # finished
def get_recent_chat_messages():
    """
    获取用户最近的聊天消息

    GET /history/recent-chat-messages?limit=10
    Authorization: Bearer <token>

    Query Parameters:
    - limit: 返回消息数量限制 (默认10)

    Response:
    {
        "messages": [
            {
                "id": 1,
                "session_id": "session_001",
                "message_type": "user",
                "content": "消息内容",
                "timestamp": "2025-01-01 12:00:00"
            }
        ],
        "total": 1,
        "limit": 10
    }
    """
    try:
        # 检查认证令牌
        token = request.headers.get('Authorization')
        user_info = None
        if token and token.startswith('Bearer '):
            token = token[7:]
            user_info = auth_service.verify_token(token)

        if not user_info:
            return jsonify({'error': '认证失败'}), 401

        # 获取查询参数
        limit = int(request.args.get('limit', 10))

        # 限制查询数量
        limit = min(limit, 50)  # 最多返回50条消息

        messages = history_db.get_recent_chat_messages(user_info['user_id'], limit)

        return jsonify({
            'messages': messages,
            'total': len(messages),
            'limit': limit
        })

    except Exception as e:
        return jsonify({'error': f'获取最近聊天消息失败: {str(e)}'}), 500