"""
AI服务模块
提供AI图片生成的核心业务逻辑
"""

import requests
import base64
import time
from utils.ai_utils import enhance_prompt

class AIService:
    """AI生成服务类"""

    def __init__(self):
        """初始化AI服务"""
        # 通义万相API配置
        self.TONGYI_API_KEY = "sk-83435cddefcc48f3b9eba7079343224b"
        self.API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"

    def generate_image(self, prompt, image_size="1024*1024", prompt_type="standard"):
        """
        生成AI图片

        Args:
            prompt (str): 生成提示词
            image_size (str): 图片尺寸，格式如"1024*1024"
            prompt_type (str): 提示词增强类型

        Returns:
            str: 生成的图片base64编码

        Raises:
            Exception: 生成失败时抛出异常
        """
        try:
            # 增强提示词
            enhanced_prompt = enhance_prompt(prompt, prompt_type)
            print(f"原始提示词: {prompt}")
            print(f"增强类型: {prompt_type}")
            print(f"增强后提示词: {enhanced_prompt}")

            # 构建API请求
            headers = {
                "Authorization": f"Bearer {self.TONGYI_API_KEY}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable"
            }

            payload = {
                "model": "wanx-v1",
                "input": {
                    "prompt": enhanced_prompt
                },
                "parameters": {
                    "size": image_size,
                    "n": 1
                }
            }

            print(f"调用通义万相API，提示词: {enhanced_prompt[:50]}...")

            # 提交任务
            response = requests.post(self.API_URL, headers=headers, json=payload, timeout=60)

            if response.status_code != 200:
                error_msg = f"API请求失败: {response.status_code}, 响应: {response.text}"
                raise Exception(error_msg)

            result = response.json()
            print(f"任务提交响应: {result}")

            # 获取任务ID
            output = result.get("output", {})
            task_id = output.get("task_id")

            if not task_id:
                raise Exception("未获取到任务ID")

            print(f"任务ID: {task_id}")

            # 轮询任务状态
            return self._poll_task_status(task_id, headers)

        except Exception as e:
            print(f"AI生成失败: {str(e)}")
            raise Exception(f"AI图片生成失败: {str(e)}")

    def _poll_task_status(self, task_id, headers, max_attempts=50):   # finished
        """
        轮询任务状态

        Args:
            task_id (str): 任务ID
            headers (dict): 请求头
            max_attempts (int): 最大轮询次数

        Returns:
            str: 生成的图片base64编码

        Raises:
            Exception: 任务失败或超时
        """
        for i in range(max_attempts):
            time.sleep(2)
            poll_message = f'轮询中... ({i+1}/{max_attempts})'
            print(poll_message)

            query_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
            query_response = requests.get(query_url, headers=headers, timeout=30)

            if query_response.status_code == 200:
                task_result = query_response.json()
                print(f"轮询响应: {task_result}")

                task_output = task_result.get("output", {})
                task_status = task_output.get("task_status")

                if task_status == "SUCCEEDED":
                    image_url = task_output["results"][0]["url"]
                    print(f"图片URL: {image_url}")

                    # 下载图片并转换为base64
                    img_response = requests.get(image_url, timeout=30)
                    img_response.raise_for_status()
                    return base64.b64encode(img_response.content).decode('utf-8')

                elif task_status == "FAILED":
                    error_message = task_output.get("message", "未知错误")
                    print(f"错误详情: {error_message}")
                    raise Exception(f"图片生成失败: {error_message}")

        raise Exception("任务处理超时")

# 创建全局AI服务实例
ai_service = AIService()
