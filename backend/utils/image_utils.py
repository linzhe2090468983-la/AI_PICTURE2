"""
图片处理工具模块
提供图片验证、处理、效果应用等功能
"""

from PIL import Image, ImageEnhance, ImageFilter

def allowed_file(filename):
    """
    检查文件扩展名是否允许

    Args:
        filename (str): 文件名

    Returns:
        bool: 是否为允许的文件类型
    """
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def apply_image_effects(img, model, style, brightness, contrast, saturation):
    """
    应用图像效果调整

    Args:
        img (PIL.Image): 原始图片
        model (str): 模型类型
        style (str): 风格类型
        brightness (int): 亮度调整值 (-50 到 50)
        contrast (int): 对比度调整值 (-50 到 50)
        saturation (int): 饱和度调整值 (-50 到 50)

    Returns:
        PIL.Image: 处理后的图片
    """
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

def preprocess_image(img):
    """
    预处理图片，转换为RGB模式

    Args:
        img (PIL.Image): 原始图片

    Returns:
        PIL.Image: 处理后的图片
    """
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

    return img
