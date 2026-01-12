"""
AI工具模块
提供AI生成相关的功能，包括提示词生成、增强等
"""

def generate_prompt(model, style, brightness, contrast, saturation, description=""):
    """
    生成AI提示词

    Args:
        model (str): 模型类型
        style (str): 风格类型
        brightness (int): 亮度值
        contrast (int): 对比度值
        saturation (int): 饱和度值
        description (str, optional): 用户描述

    Returns:
        str: 生成的提示词
    """
    if description:
        return description

    prompts = {
        'creative': f"A creative e-commerce product image in {style} style",
        'photography': f"A professional product photo in {style} composition",
        'minimalist': f"A minimalist product image in {style} layout"
    }
    return prompts.get(model, f"An e-commerce product image in {style} style")

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

def build_contextual_prompt(current_prompt, session_history):
    """
    根据会话历史构建包含上下文的完整提示词

    Args:
        current_prompt (str): 当前提示词
        session_history (list): 会话历史记录

    Returns:
        str: 包含上下文的完整提示词
    """
    if not session_history:
        return current_prompt

    # 只获取最近的几次对话，避免提示词过长
    recent_history = session_history[-10:]  # 获取最近10条消息

    context_parts = ["基于以下对话历史生成图片:"]

    for msg in recent_history:
        if msg.get('role') == 'user':
            context_parts.append(f"用户: {msg.get('content', '')}")
        elif msg.get('role') == 'assistant' and 'image_url' in msg:
            context_parts.append("助手: 生成了一张图片")

    context_parts.append(f"当前请求: {current_prompt}")
    context_parts.append("请根据以上上下文生成合适的图片")

    return "\n".join(context_parts)
