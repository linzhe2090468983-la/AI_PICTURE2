"""
图片生成路由模块
处理图片上传、AI生成、本地处理等图片相关请求
"""

import uuid
from flask import Blueprint, request, jsonify
from models.mysql_user_model import MySQLAuthService
from models.mysql_history_model import MySQLHistoryDB
from services.image_service import image_service
from services.ai_service import ai_service

# 创建图片生成蓝图
image_bp = Blueprint('image', __name__)

# 初始化服务
auth_service = MySQLAuthService()
history_db = MySQLHistoryDB()

@image_bp.route('/generate', methods=['POST'])
def generate_image():
    """
    生成宣传图片（上传图片 + AI处理）

    POST /image/generate
    Content-Type: multipart/form-data
    Authorization: Bearer <token>

    Form Data:
    - image: 图片文件
    - model: AI模型类型
    - style: 生成风格
    - brightness: 亮度调整 (-50 到 50)
    - contrast: 对比度调整 (-50 到 50)
    - saturation: 饱和度调整 (-50 到 50)
    - description: 用户描述（可选）

    Response:
    {
        "success": true,
        "image_url": "base64编码的图片",
        "filename": "生成的文件名",
        "model": "使用的模型",
        "style": "使用的风格",
        "fallback": false,
        "prompt": "使用的提示词",
        "session_id": "会话ID"
    }
    """
    try:
        # 检查认证令牌
        token = request.headers.get('Authorization')
        user_id = None
        if token and token.startswith('Bearer '):
            token = token[7:]
            user_info = auth_service.verify_token(token)
            if user_info:
                user_id = user_info['user_id']

        # 检查是否有文件上传
        if 'image' not in request.files:
            return jsonify({'error': '没有上传图片'}), 400

        # 获取上传的文件
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400

        # 获取参数
        model = request.form.get('model', 'creative')
        style = request.form.get('style', 'banner')
        description = request.form.get('description', '')

        # 获取调整参数
        try:
            brightness = int(request.form.get('brightness', 0))
            contrast = int(request.form.get('contrast', 0))
            saturation = int(request.form.get('saturation', 0))
        except ValueError:
            brightness = contrast = saturation = 0

        # 限制参数范围
        brightness = max(-50, min(50, brightness))
        contrast = max(-50, min(50, contrast))
        saturation = max(-50, min(50, saturation))

        # 生成会话ID
        session_id = request.form.get('session_id', str(uuid.uuid4()))

        # 记录请求历史
        if user_id:
            history_db.save_chat_message(user_id, session_id, 'user', f"上传图片生成请求: {description}")

        # 尝试AI生成
        try:
            # 生成提示词
            prompt = description if description else f"{model} style {style} product image"

            # 调用AI生成
            image_base64 = ai_service.generate_image(prompt)

            response_data = {
                'success': True,
                'image_url': f"data:image/png;base64,{image_base64}",
                'filename': f"ai_generated_{uuid.uuid4().hex}.png",
                'model': model,
                'style': style,
                'prompt': prompt,
                'session_id': session_id
            }

            # 保存生成记录
            if user_id:
                history_db.save_generation_record(user_id, response_data['image_url'], prompt, model, style)
                history_db.save_chat_message(user_id, session_id, 'system', f"AI生成成功: {prompt}")

            return jsonify(response_data)

        except Exception as ai_error:
            print(f"AI生成失败，使用本地处理: {ai_error}")

            # AI生成失败，使用本地处理
            try:
                image_url, filename, message = image_service.process_upload_and_generate(
                    file, model, style, brightness, contrast, saturation, description
                )

                response_data = {
                    'success': True,
                    'image_url': image_url,
                    'filename': filename,
                    'model': model,
                    'style': style,
                    'fallback': True,
                    'prompt': description or f"{model} style {style} processing",
                    'session_id': session_id
                }

                # 保存生成记录
                if user_id:
                    history_db.save_generation_record(user_id, response_data['image_url'],
                                                    response_data['prompt'], model, style)
                    history_db.save_chat_message(user_id, session_id, 'system',
                                               f"本地处理成功: {response_data['prompt']}")

                return jsonify(response_data)

            except Exception as local_error:
                # 本地处理也失败
                error_msg = f'图片处理失败: {str(local_error)}'
                if user_id:
                    history_db.save_chat_message(user_id, session_id, 'system', f"处理失败: {error_msg}")
                return jsonify({'error': error_msg}), 500

    except Exception as e:
        print(f"生成错误: {str(e)}")
        error_response = {'error': f'生成失败: {str(e)}'}
        return jsonify(error_response), 500

@image_bp.route('/generate-from-text', methods=['POST', 'OPTIONS'])   # finished
def generate_from_text():
    """
    文字描述生成图片

    POST /image/generate-from-text
    Content-Type: application/json
    Authorization: Bearer <token>

    Request Body:
    {
        "prompt": "生成图片的描述",
        "prompt_type": "standard|creative|professional",
        "image_size": "1024*1024",   该值如果前端传送值就用前端的值
        "session_id": "会话ID"
    }

    Response:
    {
        "success": true,
        "image_url": "base64编码的图片",
        "session_id": "会话ID",
        "prompt": "使用的提示词",
        "task_id": "任务ID"
    }
    """
    # 处理预检请求
    if request.method == 'OPTIONS':
        return '', 200

    try:
        # 检查认证令牌
        token = request.headers.get('Authorization')
        user_id = None
        if token and token.startswith('Bearer '):
            token = token[7:]
            user_info = auth_service.verify_token(token)
            if user_info:
                user_id = user_info['user_id']

        # 获取请求数据
        data = request.get_json()
        text = data.get('prompt', '')
        prompt_type = data.get('prompt_type', 'standard')
        image_size = data.get('image_size', '1024*1024')
        session_id = data.get('session_id', str(uuid.uuid4()))

        if not text or text.strip() == '':
            return jsonify({
                'success': False,
                'error': '没有提供有效的文本描述'
            }), 400

        print(f"开始处理生成请求: '{text}'...")
        print(f"会话ID: {session_id}")
        print(f"提示词类型: {prompt_type}")
        print(f"图片尺寸: {image_size}")

        # 保存用户请求
        if user_id:
            history_db.save_chat_message(user_id, session_id, 'user', f"文本生成请求: {text}")

        # 调用AI生成
        try:
            image_base64 = ai_service.generate_image(text, image_size, prompt_type)
            image_url = f"data:image/png;base64,{image_base64}"

            # 保存生成记录
            if user_id:
                history_db.save_generation_record(user_id, image_url, text, 'text_generation', prompt_type)
                history_db.save_chat_message(user_id, session_id, 'system', f"文本生成成功: {text}")

            response_data = {
                'success': True,
                'image_url': image_url,
                'session_id': session_id,
                'prompt': text,
                'prompt_type': prompt_type,
                'image_size': image_size
            }

            return jsonify(response_data)

        except Exception as api_error:
            print(f"API生成失败: {str(api_error)}")

            # 保存失败记录
            if user_id:
                history_db.save_chat_message(user_id, session_id, 'system', f"生成失败: {str(api_error)}")

            return jsonify({
                'success': False,
                'error': f'AI生成失败: {str(api_error)}'
            }), 500

    except Exception as e:
        print(f"整体处理错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

# 没有用到
@image_bp.route('/simple-test', methods=['POST'])   # finished
def simple_test():
    """
    简单图片效果测试（仅本地处理）

    POST /image/simple-test
    Content-Type: multipart/form-data
    Authorization: Bearer <token>

    Form Data:
    - image: 图片文件
    - brightness: 亮度调整
    - contrast: 对比度调整
    - saturation: 饱和度调整
    - description: 用户描述

    Response:
    {
        "success": true,
        "image_url": "base64编码的图片",
        "is_test": true,
        "session_id": "会话ID"
    }
    """
    try:
        # 检查认证令牌
        token = request.headers.get('Authorization')
        user_id = None
        if token and token.startswith('Bearer '):
            token = token[7:]
            user_info = auth_service.verify_token(token)
            if user_info:
                user_id = user_info['user_id']

        if 'image' not in request.files:
            return jsonify({'error': '没有上传图片'}), 400

        file = request.files['image']
        if file.filename == '' or not file:
            return jsonify({'error': '无效的文件'}), 400

        # 获取参数
        try:
            brightness = int(request.form.get('brightness', 0))
            contrast = int(request.form.get('contrast', 0))
            saturation = int(request.form.get('saturation', 0))
        except ValueError:
            brightness = contrast = saturation = 0

        # 限制参数范围
        brightness = max(-50, min(50, brightness))
        contrast = max(-50, min(50, contrast))
        saturation = max(-50, min(50, saturation))

        description = request.form.get('description', '')
        session_id = request.form.get('session_id', str(uuid.uuid4()))

        # 处理图片
        try:
            image_url, filename, message = image_service.simple_image_test(
                file, brightness, contrast, saturation, description
            )

            response_data = {
                'success': True,
                'image_url': image_url,
                'is_test': True,
                'session_id': session_id
            }

            # 保存测试记录
            if user_id:
                history_db.save_chat_message(user_id, session_id, 'user', f"简单测试: {description}")
                history_db.save_generation_record(user_id, response_data['image_url'], description, 'simple_test', 'local')
                history_db.save_chat_message(user_id, session_id, 'system', "简单测试完成")

            return jsonify(response_data)

        except Exception as e:
            error_msg = f'处理失败: {str(e)}'
            if user_id:
                history_db.save_chat_message(user_id, session_id, 'system', f"测试失败: {error_msg}")
            return jsonify({'error': error_msg}), 500

    except Exception as e:
        print(f"简单测试错误: {str(e)}")
        error_response = {'error': f'处理失败: {str(e)}'}
        return jsonify(error_response), 500
