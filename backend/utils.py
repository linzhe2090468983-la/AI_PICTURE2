from PIL import Image, ImageEnhance, ImageFilter
import base64
import io
import os
import requests
from config import AI_MODEL_CONFIGS

def allowed_file(filename):
    """检查文件扩展名是否允许
    
    Args:
        filename (str): 文件名
        
    Returns:
        bool: 如果文件扩展名允许则返回True
    """
    from config import ALLOWED_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    # 1. 文件名中是否有'.'
    # 2. 分割文件名获取扩展名
    # 3. 转小写后检查是否在允许列表中

def get_access_token_wenxinyige(api_key, secret_key):
    """获取文心一格的访问令牌
    
    Args:
        api_key (str): API密钥
        secret_key (str): 密钥
        
    Returns:
        str: 访问令牌
    """
    url = AI_MODEL_CONFIGS['wenxinyige']['url1']
    payload = {
        'grant_type': 'client_credentials',
        'client_id': api_key,
        'client_secret': secret_key
    }
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            print(f"文心一格获取访问令牌失败: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"文心一格获取访问令牌异常: {str(e)}")
    return None

def get_access_token_tongyi(api_key):
    """获取通义万相的访问令牌 - 这个API可能不需要单独获取token"""
    # 通义万相API通常直接使用API密钥进行认证
    return api_key

def validate_api_configs():
    """验证API配置是否正确"""
    configs = AI_MODEL_CONFIGS
    
    print("验证API配置...")
    
    # 验证文心一格配置
    wenxin_config = configs['wenxinyige']
    if not wenxin_config['api_key'] or not wenxin_config['secret_key']:
        print("⚠️ 文心一格: 缺少API密钥或密钥")
    else:
        print("✓ 文心一格: API密钥配置完整")
    
    # 验证通义万相配置
    tongyi_config = configs['tongyiwanxiang']
    if not tongyi_config['api_key']:
        print("⚠️ 通义万相: 缺少API密钥")
    else:
        print("✓ 通义万相: API密钥配置完整")
    
    # 验证即梦配置
    jimeng_config = configs['jimeng']
    if not jimeng_config['api_key']:
        print("⚠️ 即梦: 缺少API密钥")
    else:
        print("✓ 即梦: API密钥配置完整")

def generate_prompt(model, style, brightness, contrast, saturation):
    """根据模型和风格生成提示词
    
    Args:
        model (str): 选择的AI模型
        style (str): 选择的风格
        brightness (int): 亮度调整值
        contrast (int): 对比度调整值
        saturation (int): 饱和度调整值
        
    Returns:
        str: 生成的提示词
    """
    # 定义基础提示词模板
    model_descriptions = {
        'creative': '创意电商广告，富有想象力的设计',
        'photography': '专业摄影效果，真实自然',
        'minimalist': '极简现代设计，简洁优雅',
        'colorful': '高饱和度色彩，鲜艳夺目'
    }
    
    style_descriptions = {
        'banner': '横幅广告，宽幅设计',
        'social': '社交媒体图片，方形比例',
        'product': '产品详情页，清晰展示',
        'promotion': '促销海报，吸引眼球'
    }
    
    # 根据亮度、对比度、饱和度调整描述
    adjustment_descriptions = []
    if brightness > 10:
        adjustment_descriptions.append('明亮')
    elif brightness < -10:
        adjustment_descriptions.append('暗调')
    
    if contrast > 10:
        adjustment_descriptions.append('高对比度')
    elif contrast < -10:
        adjustment_descriptions.append('低对比度')
    
    if saturation > 10:
        adjustment_descriptions.append('高饱和度')
    elif saturation < -10:
        adjustment_descriptions.append('低饱和度')
    
    # 组合提示词
    prompt_parts = [
        model_descriptions.get(model, '电商宣传图'),
        style_descriptions.get(style, '设计图'),
        '高质量',
        '专业设计',
        *adjustment_descriptions
    ]
    
    return ', '.join(prompt_parts)

def generate_image_with_wenxinyige(prompt, image_path=None):   # finished
    """使用文心一格生成图片
    
    Args:
        prompt (str): 提示词
        image_path (str, optional): 上传的图片路径，用于图像到图像的转换
        
    Returns:
        str: 生成图片的base64数据，失败则返回None
    """
    config = AI_MODEL_CONFIGS['wenxinyige']
    if not config['api_key'] or not config['secret_key']:
        print("文心一格API配置不完整")
        return None
    
    access_token = get_access_token_wenxinyige(config['api_key'], config['secret_key'])
    if not access_token:
        print("无法获取文心一格访问令牌")
        return None
    
    url = "https://qianfan.baidubce.com/v2/images/generations"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    payload = {
        'model': 'ernie-art-4.5-8k',
        'prompt': prompt,
        'n': 1,
        'size': '1024x1024'
    }
    
    # 如果提供了图片路径，添加图像到图像的参数
    if image_path:
        # 将图片编码为base64
        with open(image_path, 'rb') as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        payload['image'] = image_base64
        payload['style'] = 'realistic'
    
    try:
        response = requests.post(url, headers=headers, json=payload) 
        if response.status_code == 200:
            result = response.json()
            if 'data' in result and 'images' in result['data'] and len(result['data']['images']) > 0:
                # 获取图片数据 - 文心一格返回的是base64编码的图片
                image_data = result['data']['images'][0]
                if isinstance(image_data, dict) and 'b64_image' in image_data:
                    return image_data['b64_image']
                elif isinstance(image_data, str):
                    return image_data
            else:
                print(f"文心一格响应中没有图片数据: {result}")
        else:
            print(f"文心一格API请求失败: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"文心一格生成错误: {str(e)}")
    
    return None

def generate_image_with_tongyiwanxiang(prompt, image_path=None):   
    """使用通义万相生成图片
    
    Args:
        prompt (str): 提示词
        image_path (str, optional): 上传的图片路径，用于图像到图像的转换
        
    Returns:
        str: 生成图片的base64数据，失败则返回None
    """
    config = AI_MODEL_CONFIGS['tongyiwanxiang']
    if not config['api_key']:
        print("通义万相API配置不完整")
        return None
    
    headers = {
        'Authorization': f'Bearer {config["api_key"]}',
        'Content-Type': 'application/json'
    }
    
    # 通义万相使用兼容模式API
    url = config['base_url'] + '/images/generations'
    
    payload = {
        'model': 'wanx-v1',  # 通义万相模型
        'prompt': prompt,
        'n': 1,
        'size': '1024*1024'
    }
    
    # 如果提供了图片路径，添加图像到图像的参数
    if image_path:
        # 将图片编码为base64
        with open(image_path, 'rb') as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        payload['image'] = image_base64
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            if 'data' in result and len(result['data']) > 0:
                # 通义万相返回的是base64编码的图片数据
                image_data = result['data'][0]
                if 'url' in image_data:
                    # 如果返回的是URL，需要下载图片
                    image_url = image_data['url']
                    image_response = requests.get(image_url)
                    if image_response.status_code == 200:
                        return base64.b64encode(image_response.content).decode('utf-8')
                elif 'b64_image' in image_data:
                    return image_data['b64_image']
                else:
                    # 直接返回图片数据
                    return image_data
            else:
                print(f"通义万相响应中没有图片数据: {result}")
        else:
            print(f"通义万相API请求失败: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"通义万相生成错误: {str(e)}")
    
    return None

def generate_image_with_jimeng(prompt, image_path=None):
    """使用即梦AI生成图片
    
    Args:
        prompt (str): 提示词
        image_path (str, optional): 上传的图片路径，用于图像到图像的转换
        
    Returns:
        str: 生成图片的base64数据，失败则返回None
    """
    config = AI_MODEL_CONFIGS['jimeng']
    if not config['api_key']:
        print("即梦API配置不完整")
        return None
    
    headers = {
        'Authorization': f'Bearer {config["api_key"]}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'prompt': prompt,
        'n': 1,
        'size': '1024x1024',
        'style': 'default'
    }
    
    # 如果提供了图片路径，添加图像到图像的参数
    if image_path:
        # 将图片编码为base64并添加到请求中
        with open(image_path, 'rb') as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        payload['image'] = image_base64  # 根据API文档添加图片参数
    
    try:
        response = requests.post(config['image_gen_url'], headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            if 'data' in result and 'images' in result['data']:
                # 即梦返回的是图片URL列表，需要下载
                image_url = result['data']['images'][0]['url']
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    return base64.b64encode(image_response.content).decode('utf-8')
            else:
                print(f"即梦响应中没有图片数据: {result}")
        else:
            print(f"即梦API请求失败: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"即梦生成错误: {str(e)}")
    
    return None

def try_ai_generation(prompt, image_path=None, description=""):
    """尝试使用不同AI模型生成图片，按优先级依次尝试
    
    Args:
        prompt (str): 提示词
        image_path (str, optional): 上传的图片路径，用于图像到图像的转换
        description (str): 用户输入的描述
        
    Returns:
        tuple: (是否成功, 生成的图片base64数据或错误信息)
    """
    # 首先验证API配置
    validate_api_configs()
    
    # 对于参考图片上传功能，只使用通义万相
    print("参考图片上传模式，仅使用通义万相生成图片...")
    result = generate_image_with_tongyiwanxiang(prompt, image_path, description)
    if result:
        print("✓ 通义万相生成成功")
        return True, result
    
    return False, "通义万相无法生成图片，请检查API配置和网络连接"

def generate_image_with_wenxinyige(prompt, image_path=None, description=""):
    """使用文心一格生成图片，支持参考图
    
    Args:
        prompt (str): 提示词
        image_path (str, optional): 上传的图片路径
        description (str): 用户输入的描述
        
    Returns:
        str: 生成图片的base64数据，失败则返回None
    """
    config = AI_MODEL_CONFIGS['wenxinyige']
    if not config['api_key'] or not config['secret_key']:
        return None
    
    access_token = get_access_token_wenxinyige(config['api_key'], config['secret_key'])
    if not access_token:
        return None
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    
    payload = {
        'model': 'ernie-vilg-v2',  
        'prompt': prompt,
        'n': 1,
        'size': '1024x1024'
    }
    
    # 如果提供了图片路径，添加图像到图像的参数
    if image_path and description:
        # 将图片编码为base64
        with open(image_path, 'rb') as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        payload['image'] = image_base64
        payload['style'] = 'realistic'  # 或其他适合的风格参数
    
    try:
        response = requests.post(config['image_gen_url'], headers=headers, json=payload) 
        if response.status_code == 200:
            result = response.json()
            if 'data' in result and 'sub_images' in result['data'] and len(result['data']['sub_images']) > 0:
                # 获取图片URL - 文心一格返回的是sub_images数组
                image_url = result['data']['sub_images'][0]['url']
                # 从URL下载图片并转换为base64
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    return base64.b64encode(image_response.content).decode('utf-8')
    except Exception as e:
        print(f"文心一格生成错误: {str(e)}")
    
    return None

def generate_image_with_tongyiwanxiang(prompt, image_path=None, description=""):
    """使用通义万相生成图片，支持参考图
    
    Args:
        prompt (str): 提示词
        image_path (str, optional): 上传的图片路径
        description (str): 用户输入的描述
        
    Returns:
        str: 生成图片的base64数据，失败则返回None
    """
    config = AI_MODEL_CONFIGS['tongyiwanxiang']
    if not config['api_key']:
        return None
    
    headers = {
        'Authorization': f'Bearer {config["api_key"]}',
        'Content-Type': 'application/json',
        'X-DashScope-Async': 'enable'
    }
    
    payload = {
        'model': 'wanx-v1',
        'input': {
            'prompt': prompt
        },
        'parameters': {
            'size': '1024*1024',
            'n': 1
        }
    }
    
    # 如果提供了图片路径，添加参考图片
    if image_path:
        # 将图片编码为base64
        with open(image_path, 'rb') as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        payload['input']['ref_image'] = f"data:image/jpeg;base64,{image_base64}"
        payload['parameters']['ref_mode'] = 'repaint'
        payload['parameters']['ref_strength'] = 0.85  # 控制参考图影响强度
    
    # 添加描述到提示词
    if description:
        payload['input']['prompt'] = f"{prompt} {description}"
    
    try:
        response = requests.post('https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis', 
                                headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            if 'output' in result and 'data' in result['output']:
                # 通义万相返回的是图片URL，需要下载
                image_url = result['output']['data'][0]['url']
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    return base64.b64encode(image_response.content).decode('utf-8')
    except Exception as e:
        print(f"通义万相生成错误: {str(e)}")
    
    return None

def generate_image_with_jimeng(prompt, image_path=None, description=""):
    """使用即梦AI生成图片，支持参考图
    
    Args:
        prompt (str): 提示词
        image_path (str, optional): 上传的图片路径
        description (str): 用户输入的描述
        
    Returns:
        str: 生成图片的base64数据，失败则返回None
    """
    config = AI_MODEL_CONFIGS['jimeng']
    if not config['api_key']:
        print("即梦API配置不完整")
        return None
    
    headers = {
        'Authorization': f'Bearer {config["api_key"]}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'prompt': prompt,
        'n': 1,
        'size': '1024x1024',
        'style': 'default'
    }
    
    # 如果提供了图片路径，添加图像到图像的参数
    if image_path:
        # 将图片编码为base64并添加到请求中
        with open(image_path, 'rb') as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        payload['image'] = image_base64  # 根据API文档添加图片参数
    
    # 添加描述到提示词
    if description:
        payload['prompt'] = f"{prompt} {description}"
    
    try:
        response = requests.post(config['image_gen_url'], headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            if 'data' in result and 'images' in result['data']:
                # 即梦返回的是图片URL列表，需要下载
                image_url = result['data']['images'][0]['url']
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    return base64.b64encode(image_response.content).decode('utf-8')
            else:
                print(f"即梦响应中没有图片数据: {result}")
        else:
            print(f"即梦API请求失败: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"即梦生成错误: {str(e)}")
    
    return None

def generate_image_from_text_ai(text_prompt):
    """
    专门用于文本输入调用AI的函数，只调用一个大模型
    """
    # 这里应该实现具体的AI调用逻辑
    # 目前使用try_ai_generation的简化版本，只调用一个模型
    try:
        # 导入AI模型相关模块
        from config import QWEN_MODEL
        from dashscope import ImageSynthesis
        import base64
        
        # 使用通义万相API生成图片
        response = ImageSynthesis.call(
            model=QWEN_MODEL,
            prompt=text_prompt,
            n=1,
            size='1024*1024'
        )
        
        if response and response.output and response.output.results:
            image_url = response.output.results[0].url
            # 从URL获取图片数据并转换为base64
            import requests
            img_data = requests.get(image_url).content
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            return True, img_base64
        else:
            return False, None
    except Exception as e:
        print(f"AI生成错误: {str(e)}")
        return False, None

def apply_image_effects(image, model, style, brightness=0, contrast=0, saturation=0):
    """应用图像效果和滤镜
    
    Args:
        image (PIL.Image): PIL图像对象
        model (str): 选择的AI模型
        style (str): 选择的风格
        brightness (int): 亮度调整值 (-50 到 50)
        contrast (int): 对比度调整值 (-50 到 50)
        saturation (int): 饱和度调整值 (-50 到 50)
        
    Returns:
        PIL.Image: 处理后的图像
    """
    # 根据模型应用不同的基础效果
    if model == 'creative':
        # 创意效果：增强色彩，添加轻微模糊
        image = image.filter(ImageFilter.SMOOTH)
        saturation += 20
    elif model == 'photography':
        # 摄影效果：增强锐度，调整色调
        image = image.filter(ImageFilter.SHARPEN)
        contrast += 10
    elif model == 'minimalist':
        # 极简效果：降低饱和度，提高亮度
        saturation -= 20
        brightness += 10
    elif model == 'colorful':
        # 多彩效果：大幅提高饱和度
        saturation += 30
    
    # 根据风格调整尺寸和添加元素
    width, height = image.size
    if style == 'banner':
        # 横幅广告：调整为横幅尺寸
        new_width = max(width, 800)
        new_height = int(new_width * 0.3)
        if new_height < 200:
            new_height = 200
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    elif style == 'social':
        # 社交媒体：方形或1:1比例
        size = max(width, height, 500)
        image = image.resize((size, size), Image.Resampling.LANCZOS)
    elif style == 'product':
        # 产品详情：保持原比例，但调整大小
        max_size = 600
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    elif style == 'promotion':
        # 促销海报：调整尺寸，添加促销效果
        image = image.resize((800, 1000), Image.Resampling.LANCZOS)
    
    # 应用亮度调整
    if brightness != 0:
        enhancer = ImageEnhance.Brightness(image)
        factor = (brightness + 100) / 100
        image = enhancer.enhance(factor)
    
    # 应用对比度调整
    if contrast != 0:
        enhancer = ImageEnhance.Contrast(image)
        factor = (contrast + 100) / 100
        image = enhancer.enhance(factor)
    
    # 应用饱和度调整
    if saturation != 0:
        enhancer = ImageEnhance.Color(image)
        factor = (saturation + 100) / 100
        image = enhancer.enhance(factor)
    
    return image