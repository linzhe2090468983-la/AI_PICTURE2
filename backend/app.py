from flask import Flask, request, jsonify, session
from flask_cors import CORS
from PIL import Image, ImageEnhance, ImageFilter
import os
import io
import base64
import uuid
import requests
import json
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import time

# 导入MySQL用户认证和历史记录模块
from models.mysql_user_model import MySQLAuthService
from models.mysql_history_model import MySQLHistoryDB
from models.database import db_connection
from services.ai_tongyi_service import try_ai_generation

app = Flask(__name__)

# 设置会话密钥
app.secret_key = 'your-secret-key'

# 启用CORS，运行所有来源的跨域请求
CORS(app)  

# 初始化MySQL认证服务和历史记录服务
auth_service = MySQLAuthService()
history_db = MySQLHistoryDB()

# 初始化数据库表
try:
    db_connection.create_tables()
    print("✅ 数据库表初始化完成")
except Exception as e:
    print(f"❌ 数据库表初始化失败: {e}")
    exit(1)

# 聊天历史存储 - 用字典存储每个会话的历史记录
chat_history = {}
image_chat_history = {}  # 新增：图片模式聊天历史

# 配置文件夹路径
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

# 确保文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def enhance_prompt(prompt, prompt_type):
    """
    根据类型增强提示词

    Args:
        prompt (str): 原始提示词
        prompt_type (str): 增强类型 ("standard", "creative", "professional")

    Returns:
        str: 增强后的提示词
    """
    if prompt_type == "creative":
        # 创意模式：添加艺术风格和创意元素
        enhanced = f"创意艺术风格，{prompt}，具有创新的设计元素，充满想象力，视觉冲击力强，艺术感十足"
    elif prompt_type == "professional":
        # 专业模式：添加商业和专业元素
        enhanced = f"专业商业风格，{prompt}，高质量，商业用途，精致制作，适合商业宣传"
    else:
        # 标准模式：保持原样或轻微优化
        enhanced = f"高质量图像，{prompt}，清晰度高，细节丰富"

    return enhanced

def generate_prompt(model, style, brightness, contrast, saturation, description=""):
    """生成AI提示词"""
    if description:
        return description
    
    prompts = {
        'creative': f"A creative e-commerce product image in {style} style",
        'vintage': f"A vintage style product photo with {style} composition",
        'modern': f"A modern minimalist product image in {style} layout"
    }
    return prompts.get(model, f"An e-commerce product image in {style} style")

def apply_image_effects(img, model, style, brightness, contrast, saturation):
    """应用图像效果"""
    # 亮度调整
    if brightness != 0:
        enhancer = ImageEnhance.Brightness(img)
        factor = (brightness + 100) / 100
        img = enhancer.enhance(factor)
    
    # 对比度调整
    if contrast != 0:
        enhancer = ImageEnhance.Contrast(img)
        factor = (contrast + 100) / 100
        img = enhancer.enhance(factor)
    
    # 饱和度调整
    if saturation != 0:
        enhancer = ImageEnhance.Color(img)
        factor = (saturation + 100) / 100
        img = enhancer.enhance(factor)
    
    # 根据风格应用滤镜
    if style == 'vintage':
        img = img.filter(ImageFilter.SMOOTH_MORE)
    elif style == 'modern':
        img = img.filter(ImageFilter.SHARPEN)
    
    return img

@app.route('/register', methods=['POST'])
def register():
    """用户注册端点"""
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

@app.route('/login', methods=['POST'])
def login():
    """用户登录端点"""
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
                    'username': username
                }
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500

@app.route('/profile', methods=['GET'])
def profile():
    """获取用户信息端点"""
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

@app.route('/generate', methods=['POST'])
def generate_image():
    """生成宣传图片的主端点
    
    Returns:
        Response: JSON响应，包含生成图片的URL或错误信息

    主API：接收图片和参数，处理后返回
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
        
        # 获取上传的文件对象
        file = request.files['image']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '文件类型不支持，请上传 PNG、JPG、JPEG 格式'}), 400
        
        # 获取参数
        model = request.form.get('model', 'creative')
        style = request.form.get('style', 'banner')
        
        # 修复：确保从前端接收到的description被正确获取和处理
        description = request.form.get('description', '')  # 获取用户输入的描述
        print(f"📝 用户输入的description: '{description}'")
        print(f"📝 description类型: {type(description)}")
        print(f"📝 description长度: {len(description)}")
        
        # 确保description不为空时才使用它
        if description and description.strip():
            description = description.strip()
            print(f"📝 清理后的description: '{description}'")
        else:
            print("⚠️  收到的description为空或仅包含空白字符")

        session_id = request.form.get('session_id', str(uuid.uuid4()))  # 获取会话ID，如果未提供则生成新的
        
        # 获取调整参数，转换为整数
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

        # 获取生成数量，默认1张，最多4张
        try:
            batch_count = int(request.form.get('batch_count', 1))
        except ValueError:
            batch_count = 1
        batch_count = max(1, min(4, batch_count))  # 限制在1-4之间
        
        # 新增：获取图片尺寸，设置默认值
        image_size = request.form.get('image_size', '1024*1024')
        
        # 验证图片尺寸是否合法
        valid_sizes = ['1024*1024', '720*1280', '768*1152', '1280*720']
        if image_size not in valid_sizes:
            image_size = '1024*1024'  # 默认值
        
        # 生成提示词 - 优先使用用户描述
        prompt = generate_prompt(model, style, brightness, contrast, saturation, description)
        print(f"生成的提示词: {prompt}")
        
        # 打印调试信息 - 显示用户选择的模型、风格和描述
        print(f"\n{'='*60}")
        print(f"🎯 图片生成请求详情:")
        print(f"📁 上传文件: {file.filename}")
        print(f"🤖 AI模型: {model}")
        print(f"🎨 生成风格: {style}")
        print(f"📝 图片描述: {description}")
        print(f"💡 亮度调整: {brightness}")
        print(f"📊 对比度调整: {contrast}")
        print(f" saturation: {saturation}")
        print(f"✨ 最终提示词: {prompt}")
        print(f"{'='*60}\n")
        
        # 管理聊天历史 - 使用图片模式聊天历史
        if session_id not in image_chat_history:
            image_chat_history[session_id] = []
        
        # 构建完整的提示词，包含历史对话上下文
        full_prompt = build_contextual_prompt(description if description else f"生成 {model} 风格的 {style} 图片", image_chat_history[session_id])
        
        # 记录用户消息 - 保存原始的 prompt 字段
        user_message = {
            'role': 'user',
            'content': description if description else f"生成 {model} 风格的 {style} 图片",
            'prompt': full_prompt,  # 保存为 prompt
            'time': datetime.now().isoformat()[:19],
            'field_used': 'description'  # 记录使用的字段
        }
        image_chat_history[session_id].append(user_message)
        
        # 保存聊天记录到数据库（如果用户已登录）
        if user_id:
            history_db.save_image_chat_message(user_id, session_id, 'user', f"图片生成请求: {description if description else f'生成 {model} 风格的 {style} 图片'}")
        
        # 生成唯一文件名，防止重名
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        upload_path = os.path.join(UPLOAD_FOLDER, filename)  # 完整上传路径
        file.save(upload_path)
        
        # 调试信息：开始AI生成
        print(f"\n{'='*60}")
        print(f"🚀 开始AI图片生成")
        print(f"📁 上传文件: {filename}")
        print(f"📝 提示词长度: {len(full_prompt)} 字符")
        print(f"📝 提示词预览: {full_prompt[:100]}...")
        print(f"{'='*60}\n")
        
        # 尝试使用AI大模型生成图片，传递上传的图片路径、描述和生成数量
        success, result = try_ai_generation(full_prompt, upload_path, description, batch_count, image_size)
        
        # 调试信息：AI生成结果
        print(f"\n{'='*60}")
        print(f"📊 AI生成结果:")
        print(f"✅ success: {success}")
        print(f"📦 result类型: {type(result)}")
        
        if success and result:
            # 处理批量生成的结果
            if isinstance(result, list):
                # 多张图片
                image_urls = []
                for i, img_result in enumerate(result):
                    print(f"📏 图片{i+1}长度: {len(img_result)} 字符")
                    print(f"👀 图片{i+1}前50字符: {img_result[:50]}")

                    # 检查是否是纯base64
                    import re
                    base64_pattern = re.compile(r'^[A-Za-z0-9+/]+=*$')
                    if img_result.startswith('data:image'):
                        print(f"🔍 检测: 图片{i+1}已经是完整的data URL")
                        img_url = img_result
                    elif base64_pattern.match(img_result[:20]):
                        print(f"🔍 检测: 图片{i+1}是纯base64格式")
                        img_url = f"data:image/png;base64,{img_result}"
                    else:
                        print(f"⚠️  检测: 图片{i+1}格式未知，尝试作为base64处理")
                        img_url = f"data:image/png;base64,{img_result}"

                    image_urls.append(img_url)

                image_url = image_urls[0]  # 主图片URL用于兼容性
            else:
                # 单张图片
                print(f"📏 result长度: {len(result)} 字符")
                print(f"👀 result前50字符: {result[:50]}")

                # 检查是否是纯base64
                import re
                base64_pattern = re.compile(r'^[A-Za-z0-9+/]+=*$')
                if result.startswith('data:image'):
                    print("🔍 检测: result已经是完整的data URL")
                    image_url = result
                elif base64_pattern.match(result[:20]):
                    print("🔍 检测: result是纯base64格式")
                    image_url = f"data:image/png;base64,{result}"
                else:
                    print("⚠️  检测: result格式未知，尝试作为base64处理")
                    image_url = f"data:image/png;base64,{result}"

                image_urls = [image_url]

            print(f"🖼️ 共生成 {len(image_urls)} 张图片")
            print(f"{'='*60}\n")

            # AI生成成功，返回图片数据
            response_data = {
                'success': True,
                'image_url': image_url,  # 主图片URL用于兼容性
                'image_urls': image_urls,  # 所有图片URL列表
                'filename': f"ai_generated_{uuid.uuid4().hex}.png",
                'model': model,
                'style': style,
                'prompt': full_prompt,
                'session_id': session_id,  # 返回会话ID
                'batch_count': len(image_urls),  # 返回实际生成的图片数量
                'generated_by': 'aliyun_ai'  # 新增：标记生成来源
            }
            
            # 调试信息：最终响应数据
            print(f"🎉 AI生成成功，准备返回数据")
            print(f"📦 image_url前80字符: {image_url[:80]}...")
            
            # 记录响应到历史（只存部分image_url，避免日志过大）
            assistant_message = {
                'role': 'assistant',
                'content': 'image_generated',
                'image_url': image_url,
                'prompt': full_prompt,  # 保存使用的提示词
                'time': datetime.now().isoformat()[:19]
            }
            image_chat_history[session_id].append(assistant_message)
            
            # 保存生成记录到数据库（如果用户已登录）
            if user_id:
                # 修复：对于批量生成的图片，应该为每张图片都保存一条记录
                for img_url in image_urls:
                    history_db.save_generation_record(user_id, img_url, full_prompt, model, style, 'image')
                history_db.save_image_chat_message(user_id, session_id, 'system', f"AI图片生成成功: {full_prompt[:50]}... 共{len(image_urls)}张")
            
            return jsonify(response_data)
        else:
            # AI生成失败，使用本地处理作为备选方案
            print(f"❌ AI生成失败，错误信息: {result}")
            print("🔄 切换到本地处理...")
            print(f"{'='*60}\n")
            
            # 打开并处理图片
            with Image.open(upload_path) as img:
                # 转换为RGB模式（如果是RGBA）
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'RGBA':
                        background.paste(img, mask=img.split()[3])
                    else:
                        background.paste(img, mask=img.split()[1])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 应用效果
                processed_img = apply_image_effects(
                    img, model, style, 
                    brightness, contrast, saturation
                )
                
                # 生成输出文件名
                output_filename = f"processed_{filename}"
                output_path = os.path.join(OUTPUT_FOLDER, output_filename)
                
                # 保存处理后的图片
                if file.filename.lower().endswith('.png'):
                    processed_img.save(output_path, 'PNG', optimize=True)
                else:
                    processed_img.save(output_path, 'JPEG', quality=90, optimize=True)
                
                # 转换为base64用于返回
                img_byte_arr = io.BytesIO()
                if file.filename.lower().endswith('.png'):
                    processed_img.save(img_byte_arr, format='PNG')
                else:
                    processed_img.save(img_byte_arr, format='JPEG')
                
                img_byte_arr.seek(0)
                img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                
                response_data = {
                    'success': True,
                    'image_url': f"data:image/png;base64,{img_base64}",
                    'filename': output_filename,
                    'model': model,
                    'style': style,
                    'prompt': full_prompt,
                    'session_id': session_id,  # 返回会话ID
                    'generated_by': 'local'  # 新增：标记为本地生成
                }
                
                # 调试信息：本地处理结果
                print(f"🛠️  本地处理成功")
                print(f"📦 image_url长度: {len(response_data['image_url'])}")
                
                # 记录响应到历史
                assistant_message = {
                    'role': 'assistant',
                    'content': 'image_generated',
                    'image_url': response_data['image_url'],
                    'prompt': full_prompt,  # 保存使用的提示词
                    'time': datetime.now().isoformat()[:19]
                }
                image_chat_history[session_id].append(assistant_message)
                
                # 保存生成记录到数据库（如果用户已登录）
                if user_id:
                    history_db.save_generation_record(user_id, response_data['image_url'], full_prompt, model, style, 'image')
                    history_db.save_image_chat_message(user_id, session_id, 'system', f"本地处理生成成功: {full_prompt[:50]}...")
                
                return jsonify(response_data)
                
    except Exception as e:
        error_msg = str(e)
        print(f"\n{'='*60}")
        print(f"💥 路由发生异常:")
        print(f"错误详情: {error_msg}")
        import traceback
        traceback.print_exc()  # 打印完整堆栈信息
        print(f"{'='*60}\n")

        # 记录错误到聊天历史
        if 'session_id' in locals() and session_id in image_chat_history:
            image_chat_history[session_id].append({
                'timestamp': datetime.now().isoformat(),
                'type': 'response',
                'success': False,
                'error': error_msg,
                'generation_type': 'image'  # 标记为图片生成
            })

            # 保存错误记录到数据库（如果用户已登录）
            if user_id:
                history_db.save_image_chat_message(user_id, session_id, 'system', f"图片生成失败: {error_msg}")

        return jsonify({'error': error_msg}), 500

@app.route('/generate-from-text', methods=['POST', 'OPTIONS'])
def generate_from_text():
    """文字描述生成图片"""
    # 处理预检请求
    if request.method == 'OPTIONS':
        return '', 200
    
    # 检查认证令牌
    token = request.headers.get('Authorization')
    user_id = None
    if token and token.startswith('Bearer '):
        token = token[7:]
        user_info = auth_service.verify_token(token)
        if user_info:
            user_id = user_info['user_id']
    
    try:
        print(f"收到请求 - 方法: {request.method}")
        print(f"请求头: {dict(request.headers)}")
        print(f"Content-Type: {request.content_type}")
        
        # 获取数据
        text = None
        session_id = None
        
        # 根据Content-Type处理不同的数据格式
        if request.content_type and 'application/json' in request.content_type:
            # JSON格式
            data = request.get_json()
            print(f"完整JSON数据: {json.dumps(data, ensure_ascii=False)}")
            
            if data:
                # 重要修改：前端发送的是 'prompt' 字段，不是 'text'
                # 优先使用 'prompt' 字段，如果没有则尝试其他字段
                text = data.get('prompt')  # 前端发送的是 prompt 字段
                
                # 如果没有 prompt 字段，尝试其他可能的字段名
                if not text:
                    text = data.get('text') or data.get('description') or data.get('input')
                
                # 获取 session_id
                session_id = data.get('session_id')

                # 获取文本生成选项
                prompt_type = data.get('prompt_type', 'standard')  # 提示词增强类型
                image_size = data.get('image_size', '1024x1024')   # 图片尺寸
                batch_count = int(data.get('batch_count', 1))     # 生成数量，默认1张
                
                print(f"提取结果:")
                print(f"  prompt字段值: {data.get('prompt')}")
                print(f"  text字段值: {data.get('text')}")
                print(f"  最终使用的text: {text}")
                print(f"  session_id: {session_id}")
                print(f"  prompt_type: {prompt_type}")
                print(f"  image_size: {image_size}")
        else:
            # 表单格式
            text = request.form.get('prompt')  # 前端发送的是 prompt 字段
            if not text:
                text = request.form.get('text') or request.form.get('description')
            session_id = request.form.get('session_id')
            print(f"表单数据提取: prompt={text}, session_id={session_id}")
        
        # 如果还没有获取到数据，尝试从原始数据解析
        if not text:
            raw_data = request.get_data(as_text=True)
            print(f"原始数据: {raw_data}")
            try:
                if raw_data and raw_data.strip():
                    data = json.loads(raw_data)
                    # 查找 prompt 字段
                    text = data.get('prompt')
                    if not text:
                        text = data.get('text') or data.get('description')
                    session_id = data.get('session_id')
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
        
        print(f"最终提取结果:")
        print(f"  text/prompt: '{text}'")
        print(f"  session_id: {session_id}")
        
        # 验证 text 是否为空
        if not text or text.strip() == '':
            error_msg = '没有提供有效的文本描述'
            print(error_msg)
            return jsonify({
                'success': False, 
                'error': error_msg,
                'received_data': {
                    'has_prompt_field': 'prompt' in str(request.get_json(silent=True)),
                    'has_text_field': 'text' in str(request.get_json(silent=True)),
                    'full_request': str(request.get_json(silent=True))[:200]
                }
            }), 400
        
        # 如果session_id为空，生成新的
        if not session_id:
            session_id = str(uuid.uuid4())
            print(f"生成新的session_id: {session_id}")
        
        print(f"开始处理生成请求: '{text}'...")
        print(f"会话ID: {session_id}")
        
        # 管理聊天历史
        if session_id not in chat_history:
            chat_history[session_id] = []
            print(f"创建新的会话历史")
        
        # 获取会话历史并整合到当前请求中
        session_history = chat_history.get(session_id, [])
        print(f"当前会话历史长度: {len(session_history)}")
        
        # 构建完整的提示词，包含历史对话上下文
        full_prompt = build_contextual_prompt(text, session_history)
        
        # 记录用户消息 - 保存原始的 prompt 字段
        user_message = {
            'role': 'user',
            'content': text,
            'prompt': text,  # 保存为 prompt
            'time': datetime.now().isoformat()[:19],
            'field_used': 'prompt'  # 记录使用的字段
        }
        chat_history[session_id].append(user_message)
        
        # 保存聊天记录到数据库（如果用户已登录）
        if user_id:
            history_db.save_chat_message(user_id, session_id, 'user', f"文本生成请求: {text}")
        
        print(f"用户消息已记录，历史长度: {len(chat_history[session_id])}")
        
        # 调用AI生成图片
        print("正在调用通义万相API生成图片...")
        try:
            # 前端已经发送正确格式的尺寸，直接使用
            api_image_size = image_size if image_size else "1024*1024"
            print(f"使用的图片尺寸: {api_image_size}")
            image_base64 = generate_with_qwen(full_prompt, api_image_size, prompt_type, batch_count)
        except Exception as api_error:
            print(f"API生成失败: {str(api_error)}")
            # 记录失败
            chat_history[session_id].append({
                'role': 'assistant',
                'content': f'生成失败: {str(api_error)}',
                'time': datetime.now().isoformat()[:19],
                'error': True
            })
            
            # 保存失败记录到数据库（如果用户已登录）
            if user_id:
                history_db.save_chat_message(user_id, session_id, 'system', f"生成失败: {str(api_error)}")
            
            return jsonify({
                'success': False,
                'error': f'AI生成失败: {str(api_error)}',
                'session_id': session_id
            }), 500
        
        if not image_base64:
            error_msg = 'AI生成失败，未返回图片数据'
            print(error_msg)
            chat_history[session_id].append({
                'role': 'assistant',
                'content': error_msg,
                'time': datetime.now().isoformat()[:19],
                'error': True
            })

            # 保存失败记录到数据库（如果用户已登录）
            if user_id:
                history_db.save_chat_message(user_id, session_id, 'system', error_msg)

            return jsonify({
                'success': False,
                'error': error_msg,
                'session_id': session_id
            }), 500

        # 处理批量生成的结果
        if isinstance(image_base64, list):
            # 多张图片
            image_urls = [f"data:image/png;base64,{img_b64}" for img_b64 in image_base64]
            image_url = image_urls[0]  # 主图片URL用于兼容性
        else:
            # 单张图片
            image_url = f"data:image/png;base64,{image_base64}"
            image_urls = [image_url]
        
        # 记录AI响应
        assistant_message = {
            'role': 'assistant',
            'content': 'image_generated',
            'image_url': image_url,
            'prompt': text,  # 保存使用的提示词
            'time': datetime.now().isoformat()[:19]
        }
        chat_history[session_id].append(assistant_message)
        
        # 保存生成记录到数据库（如果用户已登录）
        if user_id:
            # 修复：对于批量生成的图片，应该为每张图片都保存一条记录
            for img_url in image_urls:
                history_db.save_generation_record(user_id, img_url, text, generation_type='text')
            history_db.save_chat_message(user_id, session_id, 'system', f"文本生成图片成功: {text}")
        
        print(f"生成成功，历史长度: {len(chat_history[session_id])}")
        
        # 返回结果 - 返回 prompt 字段，与前端的字段名保持一致
        response_data = {
            'success': True,
            'image_url': image_url,  # 主图片URL用于兼容性
            'image_urls': image_urls,  # 所有图片URL列表
            'session_id': session_id,
            'prompt': text,  # 返回 prompt 字段，与前端保持一致
            'batch_count': len(image_urls),  # 返回实际生成的图片数量
            'history_length': len(chat_history[session_id])
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"整体处理错误: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

def build_contextual_prompt(current_prompt, session_history):
    """
    根据会话历史构建包含上下文的完整提示词
    """
    if not session_history:
        return current_prompt
    
    # 只获取最近的几次对话，避免提示词过长
    recent_history = session_history[-4:]  # 获取最近4条消息
    
    context_parts = ["基于以下对话历史生成图片:"]
    
    for msg in recent_history:
        if msg.get('role') == 'user':
            context_parts.append(f"用户: {msg.get('content', '')}")
        elif msg.get('role') == 'assistant' and 'image_url' in msg:
            context_parts.append("助手: 生成了一张图片")
    
    context_parts.append(f"当前请求: {current_prompt}")
    context_parts.append("请根据以上上下文生成合适的图片")
    
    return "\n".join(context_parts)

def generate_with_qwen(text, image_size="1024*1024", prompt_type="standard", batch_count=1):
    """
    使用通义万相API生成图片

    Args:
        text (str): 生成图片的提示词
        image_size (str): 图片尺寸，格式如"1024*1024"
        prompt_type (str): 提示词增强类型 ("standard", "creative", "professional")
        batch_count (int): 生成图片的数量，默认1张
    """
    try:
        # API配置
        TONGYI_API_KEY = "sk-83435cddefcc48f3b9eba7079343224b"
        API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
        
        headers = {
            "Authorization": f"Bearer {TONGYI_API_KEY}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable"
        }
        
        # 根据prompt_type增强提示词
        enhanced_prompt = enhance_prompt(text, prompt_type)
        print(f"原始提示词: {text}")
        print(f"增强类型: {prompt_type}")
        print(f"增强后提示词: {enhanced_prompt}")
        
        # 修正：使用正确的尺寸格式
        payload = {
            "model": "wanx-v1",
            "input": {
                "prompt": enhanced_prompt
            },
            "parameters": {
                "size": image_size,  # 使用前端选择的尺寸
                "n": batch_count  # 使用用户选择的生成数量
            }
        }
        
        print(f"调用通义万相API，提示词: {text}")
        
        # 提交任务
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            raise Exception(f"API请求失败: {response.status_code}, 响应: {response.text}")
        
        result = response.json()
        print(f"任务提交响应: {json.dumps(result, ensure_ascii=False)}")
        
        # 获取任务ID
        output = result.get("output", {})
        task_id = output.get("task_id")
        
        if not task_id:
            raise Exception("未获取到任务ID")
        
        print(f"任务ID: {task_id}")
        
        # 轮询任务状态
        for i in range(50):
            time.sleep(2)
            print(f"轮询中... ({i+1}/50)")
            
            query_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
            query_response = requests.get(query_url, headers=headers, timeout=30)
            
            if query_response.status_code == 200:
                task_result = query_response.json()
                print(f"轮询响应: {json.dumps(task_result, ensure_ascii=False)}")
                
                task_output = task_result.get("output", {})
                task_status = task_output.get("task_status")
                
                if task_status == "SUCCEEDED":
                    results = task_output["results"]
                    image_base64_list = []

                    # 处理所有生成的结果
                    for i, result in enumerate(results):
                        image_url = result["url"]
                        print(f"图片{i+1} URL: {image_url}")
                        # 下载图片
                        img_response = requests.get(image_url, timeout=30)
                        img_response.raise_for_status()
                        # 转换为base64
                        image_base64 = base64.b64encode(img_response.content).decode('utf-8')
                        image_base64_list.append(image_base64)

                    # 如果只生成一张图片，返回单个base64；否则返回列表
                    return image_base64_list if len(image_base64_list) > 1 else image_base64_list[0]
                
                elif task_status == "FAILED":
                    error_message = task_output.get("message", "未知错误")
                    print(f"错误详情: {error_message}")
                    raise Exception(f"图片生成失败: {error_message}")
        
        raise Exception("任务处理超时")
            
    except Exception as e:
        print(f"AI生成失败: {str(e)}")
        raise Exception(f"AI图片生成失败: {str(e)}")

@app.route('/simple_test', methods=['POST'])
def simple_test():
    """简单风格测试端点（无需调用大模型）"""
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
        
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': '无效的文件'}), 400
        
        # 获取调整参数
        try:
            brightness = int(request.form.get('brightness', 0))
            contrast = int(request.form.get('contrast', 0))
            saturation = int(request.form.get('saturation', 0))
        except ValueError:
            brightness = contrast = saturation = 0
        
        # 获取用户输入的描述
        description = request.form.get('description', '')
        session_id = request.form.get('session_id', str(uuid.uuid4()))
        
        # 限制参数范围
        brightness = max(-50, min(50, brightness))
        contrast = max(-50, min(50, contrast))
        saturation = max(-50, min(50, saturation))
        
        # 记录聊天历史
        if session_id not in chat_history:
            chat_history[session_id] = []
        chat_history[session_id].append({
            'timestamp': datetime.now().isoformat(),
            'type': 'request',
            'description': description,
            'brightness': brightness,
            'contrast': contrast,
            'saturation': saturation,
            'image_uploaded': True
        })
        
        # 保存聊天记录到数据库（如果用户已登录）
        if user_id:
            history_db.save_chat_message(user_id, session_id, 'user', f"简单测试请求: {description}")
        
        # 处理图片
        with Image.open(file) as img:
            # 转换为RGB模式
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])
                else:
                    background.paste(img, mask=img.split()[1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 应用调整
            if brightness != 0:
                enhancer = ImageEnhance.Brightness(img)
                factor = (brightness + 100) / 100
                img = enhancer.enhance(factor)
            
            if contrast != 0:
                enhancer = ImageEnhance.Contrast(img)
                factor = (contrast + 100) / 100
                img = enhancer.enhance(factor)
            
            if saturation != 0:
                enhancer = ImageEnhance.Color(img)
                factor = (saturation + 100) / 100
                img = enhancer.enhance(factor)
            
            # 转换为base64
            img_byte_arr = io.BytesIO()
            if file.filename.lower().endswith('.png'):
                img.save(img_byte_arr, format='PNG')
                mime_type = 'image/png'
            else:
                img.save(img_byte_arr, format='JPEG', quality=90)
                mime_type = 'image/jpeg'
            
            img_byte_arr.seek(0)
            img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
            data_url = f"data:{mime_type};base64,{img_base64}"
            
            response_data = {
                'success': True,
                'image_url': data_url,
                'is_test': True,
                'session_id': session_id  # 返回会话ID
            }
            # 记录响应到历史
            chat_history[session_id].append({
                'timestamp': datetime.now().isoformat(),
                'type': 'response',
                'success': True,
                'image_url': response_data['image_url']
            })
            
            # 保存生成记录到数据库（如果用户已登录）
            if user_id:
                history_db.save_generation_record(user_id, response_data['image_url'], description)
                history_db.save_chat_message(user_id, session_id, 'system', f"简单测试生成成功: {description}")
            
            return jsonify(response_data)
    
    except Exception as e:
        print(f"简单测试错误: {str(e)}")
        error_response = {'error': f'处理失败: {str(e)}'}
        if 'session_id' in locals():
            chat_history[session_id].append({
                'timestamp': datetime.now().isoformat(),
                'type': 'response',
                'success': False,
                'error': str(e)
            })
        return jsonify(error_response), 500

@app.route('/chat_history', methods=['GET'])
def get_all_sessions():
    """获取所有会话ID列表"""
    # 检查认证令牌
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return jsonify({'error': '缺少认证令牌'}), 401
    
    token = token[7:]
    user_info = auth_service.verify_token(token)
    if not user_info:
        return jsonify({'error': '认证失败'}), 401
    
    # 从数据库获取用户会话
    user_sessions = history_db.get_user_sessions(user_info['user_id'])
    
    return jsonify({
        'sessions': user_sessions,
        'total_sessions': len(user_sessions)
    })

@app.route('/chat_history/<session_id>', methods=['GET'])
def get_chat_history(session_id):
    """获取特定会话的聊天历史"""
    # 检查认证令牌
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return jsonify({'error': '缺少认证令牌'}), 401
    
    token = token[7:]
    user_info = auth_service.verify_token(token)
    if not user_info:
        return jsonify({'error': '认证失败'}), 401
    
    # 从数据库获取聊天历史
    chat_records = history_db.get_chat_history(user_info['user_id'], session_id)
    
    return jsonify({
        'session_id': session_id,
        'history': chat_records,
        'total_messages': len(chat_records)
    })

# 新增：获取图片模式聊天历史
@app.route('/history/recent-image-chat-messages', methods=['GET'])
def get_recent_image_chat_messages():
    """获取最近的图片模式聊天消息"""
    # 检查认证令牌
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return jsonify({'error': '缺少认证令牌'}), 401
    
    token = token[7:]
    user_info = auth_service.verify_token(token)
    if not user_info:
        return jsonify({'error': '认证失败'}), 401
    
    # 获取分页参数
    limit = int(request.args.get('limit', 10))
    
    # 从数据库获取最近的图片模式聊天历史
    chat_records = history_db.get_recent_image_chat_messages(user_info['user_id'], limit)
    
    return jsonify({
        'messages': chat_records,
        'total_messages': len(chat_records)
    })

@app.route('/chat_history/<session_id>', methods=['DELETE'])
def delete_chat_history(session_id):
    """清除特定会话的聊天历史"""
    # 检查认证令牌
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return jsonify({'error': '缺少认证令牌'}), 401
    
    token = token[7:]
    user_info = auth_service.verify_token(token)
    if not user_info:
        return jsonify({'error': '认证失败'}), 401
    
    success = history_db.delete_chat_history(user_info['user_id'], session_id)
    if success:
        return jsonify({'success': True, 'message': '会话历史已清除'})
    else:
        return jsonify({'error': '删除失败'}), 500

@app.route('/user/generation_records', methods=['GET'])
def get_user_generation_records():
    """获取用户生成记录"""
    # 检查认证令牌
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return jsonify({'error': '缺少认证令牌'}), 401
    
    token = token[7:]
    user_info = auth_service.verify_token(token)
    if not user_info:
        return jsonify({'error': '认证失败'}), 401
    
    # 获取分页参数
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    records = history_db.get_user_generation_records(user_info['user_id'], limit, offset)
    
    return jsonify({
        'records': records,
        'total': len(records)
    })

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'service': 'AI电商宣传图生成器',
        'version': '1.0.0',
        'upload_folder': os.path.abspath(UPLOAD_FOLDER),
        'output_folder': os.path.abspath(OUTPUT_FOLDER)
    })

@app.route('/', methods=['GET'])
def index():
    """根路径 - API信息"""
    return {
        'message': 'AI电商宣传图生成器 API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'register': '/register',
            'login': '/login',
            'profile': '/profile',
            'generate': '/generate',
            'generate-from-text': '/generate-from-text',
            'simple_test': '/simple_test',
            'chat_history': '/chat_history/<session_id>',
            'all_sessions': '/chat_history',
            'generation_records': '/user/generation_records'
        }
    }

# 新增：历史图片调节路由
@app.route('/simple_adjust', methods=['POST'])
def simple_adjust():
    """简单调节历史图片"""
    try:
        # 检查认证令牌
        token = request.headers.get('Authorization')
        user_id = None
        if token and token.startswith('Bearer '):
            token = token[7:]
            user_info = auth_service.verify_token(token)
            if user_info:
                user_id = user_info['user_id']
        
        # 获取参数
        image_url = request.form.get('image')
        brightness = int(request.form.get('brightness', 0))
        contrast = int(request.form.get('contrast', 0))
        saturation = int(request.form.get('saturation', 0))
        
        # 限制参数范围
        brightness = max(-50, min(50, brightness))
        contrast = max(-50, min(50, contrast))
        saturation = max(-50, min(50, saturation))
        
        # 从URL下载图片
        response = requests.get(image_url)
        if response.status_code != 200:
            return jsonify({'success': False, 'error': '无法下载图片'}), 400
        
        # 打开图片
        img = Image.open(io.BytesIO(response.content))
        
        # 转换为RGB模式（如果是RGBA）
        if img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'RGBA':
                background.paste(img, mask=img.split()[3])
            else:
                background.paste(img, mask=img.split()[1])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 应用效果
        processed_img = apply_image_effects(
            img, 'creative', 'banner', 
            brightness, contrast, saturation
        )
        
        # 转换为base64
        img_byte_arr = io.BytesIO()
        processed_img.save(img_byte_arr, format='JPEG', quality=90)
        img_byte_arr.seek(0)
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
        data_url = f"data:image/jpeg;base64,{img_base64}"
        
        response_data = {
            'success': True,
            'image_url': data_url,
            'is_adjusted': True
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"简单调节错误: {str(e)}")
        return jsonify({'success': False, 'error': f'处理失败: {str(e)}'}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 AI电商宣传图生成器后端服务启动中...")
    print("📊 服务版本: 1.0.0")
    print("💾 数据库: MySQL")
    print("🤖 AI服务: 通义万相")
    print()
    print("📋 可用端点:")
    print("  🔐 认证相关:")
    print("    POST /register        用户注册")
    print("    POST /login           用户登录")
    print("    GET  /profile         获取用户信息")
    print()
    print("  🖼️  图片生成:")
    print("    POST /generate        上传图片生成宣传图")
    print("    POST /generate-from-text  文字描述生成图片")
    print("    POST /simple_test     简单图片效果测试")
    print()
    print("  📚 历史记录:")
    print("    GET  /chat_history           获取所有会话列表")
    print("    GET  /chat_history/<id>      获取特定会话的聊天历史")
    print("    DELETE /chat_history/<id>    删除聊天历史")
    print("    GET  /user/generation_records 获取生成记录")
    print()
    print("  🏥 系统状态:")
    print("    GET  /health          健康检查")
    print("    GET  /                API信息")
    print()
    print("🌐 前端访问: http://localhost:8000")
    print("🔗 后端API: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug = False, host = '0.0.0.0', port = 5000)