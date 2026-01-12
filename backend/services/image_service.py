"""
图片生成服务模块
提供图片上传、处理、本地生成等功能
"""

import os
import io
import uuid
import base64
from PIL import Image, ImageEnhance
from utils.image_utils import allowed_file, apply_image_effects, preprocess_image
from utils.ai_utils import generate_prompt

class ImageService:
    """图片生成服务类"""

    def __init__(self, upload_folder='uploads', output_folder='outputs'):
        """
        初始化图片服务

        Args:
            upload_folder (str): 上传文件夹路径
            output_folder (str): 输出文件夹路径
        """
        self.upload_folder = upload_folder
        self.output_folder = output_folder

        # 确保文件夹存在
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)

    def process_upload_and_generate(self, file, model, style, brightness, contrast, saturation, description=""):
        """
        处理上传图片并生成宣传图

        Args:
            file: 上传的文件对象
            model (str): AI模型类型
            style (str): 生成风格
            brightness (int): 亮度调整
            contrast (int): 对比度调整
            saturation (int): 饱和度调整
            description (str): 用户描述

        Returns:
            tuple: (image_url, filename, success_message)
        """
        # 验证文件
        if not file or not allowed_file(file.filename):
            raise ValueError("不支持的文件格式，请上传 PNG、JPG、JPEG 或 GIF 格式")

        # 生成唯一文件名
        filename = f"{uuid.uuid4().hex}_{file.filename}"
        upload_path = os.path.join(self.upload_folder, filename)

        # 保存上传的文件
        file.save(upload_path)

        try:
            # 处理图片
            with Image.open(upload_path) as img:
                # 预处理图片
                processed_img = preprocess_image(img)

                # 应用效果
                final_img = apply_image_effects(
                    processed_img, model, style,
                    brightness, contrast, saturation
                )

                # 保存处理后的图片
                output_filename = f"generated_{filename}"
                output_path = os.path.join(self.output_folder, output_filename)

                # 根据原始格式保存
                if file.filename.lower().endswith('.png'):
                    final_img.save(output_path, 'PNG', optimize=True)
                    mime_type = 'image/png'
                else:
                    final_img.save(output_path, 'JPEG', quality=90, optimize=True)
                    mime_type = 'image/jpeg'

                # 转换为base64用于返回
                img_byte_arr = io.BytesIO()
                if file.filename.lower().endswith('.png'):
                    final_img.save(img_byte_arr, format='PNG')
                else:
                    final_img.save(img_byte_arr, format='JPEG')

                img_byte_arr.seek(0)
                img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                data_url = f"data:{mime_type};base64,{img_base64}"

                return data_url, output_filename, "图片处理成功"

        except Exception as e:
            raise Exception(f"图片处理失败: {str(e)}")

    def simple_image_test(self, file, brightness, contrast, saturation, description=""):
        """
        简单的图片效果测试（不调用AI）

        Args:
            file: 上传的文件对象
            brightness (int): 亮度调整
            contrast (int): 对比度调整
            saturation (int): 饱和度调整
            description (str): 用户描述

        Returns:
            tuple: (image_url, filename, success_message)
        """
        # 验证文件
        if not file or not allowed_file(file.filename):
            raise ValueError("不支持的文件格式")

        # 处理图片
        with Image.open(file) as img:
            # 预处理图片
            processed_img = preprocess_image(img)

            # 应用调整
            if brightness != 0:
                enhancer = ImageEnhance.Brightness(processed_img)
                factor = (brightness + 100) / 100
                processed_img = enhancer.enhance(factor)

            if contrast != 0:
                enhancer = ImageEnhance.Contrast(processed_img)
                factor = (contrast + 100) / 100
                processed_img = enhancer.enhance(factor)

            if saturation != 0:
                enhancer = ImageEnhance.Color(processed_img)
                factor = (saturation + 100) / 100
                processed_img = enhancer.enhance(factor)

            # 转换为base64
            img_byte_arr = io.BytesIO()
            if file.filename.lower().endswith('.png'):
                processed_img.save(img_byte_arr, format='PNG')
                mime_type = 'image/png'
            else:
                processed_img.save(img_byte_arr, format='JPEG', quality=90)
                mime_type = 'image/jpeg'

            img_byte_arr.seek(0)
            img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
            data_url = f"data:{mime_type};base64,{img_base64}"

            return data_url, f"test_{uuid.uuid4().hex}.png", "简单测试完成"

# 创建全局图片服务实例
image_service = ImageService()
