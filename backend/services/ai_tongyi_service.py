"""
阿里云通义万相AI图片生成服务
优化版本，消除HTTPS警告，增加重试机制
"""
import os
import base64
import time
import requests
import urllib3
from typing import Tuple, Optional
from dotenv import load_dotenv

# 禁用HTTPS警告（因为阿里云API可能需要）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 加载环境变量
load_dotenv()

# 阿里云API配置
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
API_URL = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis'

def try_ai_generation(prompt: str, image_path: str = None, description: str = "", n: int = 1) -> Tuple[bool, Optional[str]]:
    """
    尝试使用阿里云通义万相AI生成图片
    接口与原有 try_ai_generation 完全一致
    
    Args:
        prompt: AI生成提示词
        image_path: 参考图片路径（可选）
        description: 用户描述（可选）
        
    Returns:
        tuple: (success, result) - success为True时result是base64图片，为False时result是None
    """
    try:
        # 检查API密钥
        if not DASHSCOPE_API_KEY:
            print("❌ 未配置阿里云API密钥，请在.env文件中设置 DASHSCOPE_API_KEY")
            return False, None
        
        print("=" * 50)
        print("🤖 开始调用阿里云通义万相AI...")
        print(f"📝 提示词: {prompt[:100]}...")
        
        # 准备请求数据
        json_data = {
            'model': 'wanx-v1',
            'input': {
                'prompt': prompt,
            },
            'parameters': {
                'size': '1024*1024',
                'style': '<auto>',
                'n': n,  # 使用传入的生成数量参数
                'seed': int(time.time() % 100000),
            }
        }
        
        # 如果有参考图片
        if image_path and os.path.exists(image_path):
            try:
                print("🖼️  检测到参考图片，正在处理...")
                with open(image_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                
                json_data['input']['ref_image'] = f'data:image/jpeg;base64,{image_data}'
                json_data['parameters']['ref_mode'] = 'repaint'
                json_data['parameters']['ref_strength'] = 0.6
                print("✅ 参考图片已添加到请求")
            except Exception as e:
                print(f"⚠️  参考图片处理失败: {e}")
        
        # 准备请求头
        headers = {
            'Authorization': f'Bearer {DASHSCOPE_API_KEY}',
            'X-DashScope-Async': 'enable',
            'Content-Type': 'application/json',
        }
        
        # 发送生成请求（最多重试2次）
        max_retries = 2
        for retry in range(max_retries + 1):
            try:
                print(f"🚀 发送AI生成请求...{'（重试 ' + str(retry) + '）' if retry > 0 else ''}")
                response = requests.post(
                    API_URL,
                    headers=headers,
                    json=json_data,
                    timeout=30,
                    verify=False  
                )
                
                if response.status_code == 200:
                    break  # 成功，跳出重试循环
                elif retry < max_retries:
                    print(f"❌ 请求失败，状态码: {response.status_code}，{retry+1}秒后重试...")
                    time.sleep(retry + 1)
                    continue
                else:
                    print(f"❌ API请求失败，状态码: {response.status_code}")
                    print(f"错误信息: {response.text[:200]}")
                    return False, None
                    
            except requests.exceptions.Timeout:
                if retry < max_retries:
                    print(f"⏰ 请求超时，{retry+1}秒后重试...")
                    time.sleep(retry + 1)
                    continue
                else:
                    print("⏰ AI服务请求超时")
                    return False, None
            except requests.exceptions.ConnectionError:
                if retry < max_retries:
                    print(f"🔌 连接错误，{retry+1}秒后重试...")
                    time.sleep(retry + 1)
                    continue
                else:
                    print("🔌 网络连接失败")
                    return False, None
        
        result = response.json()
        
        # 检查任务是否创建成功
        if 'output' in result and 'task_id' in result['output']:
            task_id = result['output']['task_id']
            print(f"✅ AI任务创建成功")
            print(f"📋 任务ID: {task_id}")
            
            # 轮询获取结果
            print("⏳ 开始轮询生成结果...")
            ai_image_base64 = _poll_task_result(task_id)
            
            if ai_image_base64:
                print("🎉 AI图片生成成功！")
                print(f"📦 图片大小: {len(ai_image_base64) / 1024:.1f}KB")
                print("=" * 50)
                return True, ai_image_base64
            else:
                print("❌ AI图片生成失败")
                print("=" * 50)
                return False, None
        else:
            error_msg = result.get('message', '未知错误')
            print(f"❌ 任务创建失败: {error_msg}")
            print("=" * 50)
            return False, None
            
    except Exception as e:
        print(f"💥 AI生成异常: {str(e)}")
        print("=" * 50)
        return False, None

def _poll_task_result(task_id: str, max_attempts: int = 25, interval: int = 1) -> Optional[str]:
    """
    轮询任务结果
    
    Args:
        task_id: 任务ID
        max_attempts: 最大轮询次数
        interval: 轮询间隔(秒)
        
    Returns:
        base64编码的图片数据，失败返回None
    """
    poll_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
    headers = {
        'Authorization': f'Bearer {DASHSCOPE_API_KEY}',
        'Content-Type': 'application/json',
    }
    
    for attempt in range(max_attempts):
        try:
            # 等待一段时间
            time.sleep(interval)
            
            # 当前轮询进度
            progress = f"[{attempt+1}/{max_attempts}]"
            print(f"🔄 {progress} 查询任务状态...")
            
            # 查询任务状态
            response = requests.get(poll_url, headers=headers, timeout=15, verify=False)
            
            if response.status_code != 200:
                print(f"⚠️  查询失败，状态码: {response.status_code}")
                continue
            
            result = response.json()
            task_status = result.get('output', {}).get('task_status', 'UNKNOWN')
            print(f"📊 任务状态: {task_status}")
            
            # 成功状态
            if task_status == 'SUCCEEDED':
                results = result.get('output', {}).get('results', [])
                if results:
                    image_base64_list = []
                    for i, result_item in enumerate(results):
                        if result_item.get('url'):
                            print(f"📷 获取到生成图片{i+1} URL")
                            # 下载图片并转换为base64
                            image_base64 = _download_image(result_item['url'])
                            if image_base64:
                                image_base64_list.append(image_base64)

                    # 返回结果：单张图片返回字符串，多张图片返回列表
                    if len(image_base64_list) == 1:
                        return image_base64_list[0]
                    elif len(image_base64_list) > 1:
                        return image_base64_list
                    else:
                        print("❌ 未找到生成的图片")
                        return None
                else:
                    print("❌ 未找到生成的图片")
                    return None
            
            # 失败状态
            elif task_status in ('FAILED', 'CANCELED'):
                error_msg = result.get('message', task_status)
                print(f"❌ 任务执行失败: {error_msg}")
                return None
            
            # PENDING/RUNNING 状态继续轮询
            
        except requests.exceptions.Timeout:
            print(f"⏰ 第{attempt+1}次查询超时")
        except Exception as e:
            print(f"⚠️  第{attempt+1}次查询异常: {e}")
    
    print("⏰ 轮询超时，未获取到结果")
    return None

def _download_image(image_url: str) -> Optional[str]:
    """
    下载图片并转换为base64
    
    Args:
        image_url: 图片URL
        
    Returns:
        base64编码的图片数据
    """
    try:
        print(f"📥 开始下载图片...")
        
        # 下载图片（最多重试2次）
        max_retries = 2
        for retry in range(max_retries + 1):
            try:
                response = requests.get(image_url, timeout=60, verify=False)
                
                if response.status_code == 200:
                    break  # 成功，跳出重试循环
                elif retry < max_retries:
                    print(f"❌ 下载失败，状态码: {response.status_code}，{retry+1}秒后重试...")
                    time.sleep(retry + 1)
                    continue
                else:
                    print(f"❌ 图片下载失败，状态码: {response.status_code}")
                    return None
                    
            except requests.exceptions.Timeout:
                if retry < max_retries:
                    print(f"⏰ 下载超时，{retry+1}秒后重试...")
                    time.sleep(retry + 1)
                    continue
                else:
                    print("⏰ 图片下载超时")
                    return None
        
        # 检查是否为图片
        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type:
            print(f"⚠️  下载的内容不是图片: {content_type}")
        
        # 转换为base64
        image_base64 = base64.b64encode(response.content).decode('utf-8')
        
        # 验证图片大小
        img_size = len(image_base64) / 1024  # KB
        print(f"✅ 图片下载成功，大小: {img_size:.1f}KB")
        
        return image_base64
        
    except Exception as e:
        print(f"❌ 图片下载失败: {e}")
        return None

# 服务状态检查
def check_ai_service_status() -> dict:
    """
    检查AI服务状态
    
    Returns:
        dict: 包含服务状态信息
    """
    status = {
        'available': bool(DASHSCOPE_API_KEY),
        'api_key_configured': bool(DASHSCOPE_API_KEY and DASHSCOPE_API_KEY != 'your_api_key_here'),
        'service_name': '阿里云通义万相',
        'model': 'wanx-v1',
    }
    
    if not status['available']:
        status['message'] = '请配置DASHSCOPE_API_KEY环境变量'
    elif not status['api_key_configured']:
        status['message'] = 'API密钥未正确配置'
    else:
        status['message'] = 'AI服务可用'
    
    return status

# 测试函数
def test_ai_service():
    """测试AI服务是否正常"""
    print("🧪 测试阿里云AI服务...")
    
    status = check_ai_service_status()
    if not status['available']:
        print("❌ AI服务不可用")
        print(f"原因: {status.get('message', '未知')}")
        return False
    
    print(f"✅ API密钥: {'已配置' if status['api_key_configured'] else '未配置'}")
    print(f"📡 服务: {status['service_name']}")
    print(f"🤖 模型: {status['model']}")
    
    # 使用一个简单的测试提示词
    test_prompt = "一只可爱的小猫，阳光明媚，草地"
    print(f"\n📝 测试提示词: {test_prompt}")
    
    success, result = try_ai_generation(test_prompt)
    
    if success:
        print("\n✅ AI服务测试通过")
        return True
    else:
        print("\n❌ AI服务测试失败")
        return False

if __name__ == "__main__":
    test_ai_service()