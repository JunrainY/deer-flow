"""
视觉识别工具

基于OpenAI Vision API的截图分析和UI元素识别工具
支持页面布局理解、元素定位建议等功能
"""

import base64
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import asyncio

import httpx
from pydantic import BaseModel

from ..models.low_code_models import VisualAnalysisResult
from ..utils.json_utils import safe_json_loads


logger = logging.getLogger(__name__)


class VisionConfig(BaseModel):
    """视觉模型配置"""
    api_key: str
    endpoint: str = "https://api.openai.com/v1"
    model: str = "gpt-4-vision-preview"
    max_tokens: int = 4096
    temperature: float = 0.1
    timeout: int = 30


class UIElement(BaseModel):
    """UI元素模型"""
    type: str  # button, input, select, etc.
    text: Optional[str] = None
    position: Dict[str, int]  # x, y, width, height
    attributes: Dict[str, Any] = {}
    confidence: float = 0.0
    suggested_selector: Optional[str] = None


class VisualRecognition:
    """视觉识别工具类"""
    
    def __init__(self, config: Optional[VisionConfig] = None):
        """初始化视觉识别工具"""
        self.config = config or self._load_config()
        self.client = httpx.AsyncClient(timeout=self.config.timeout)
        
    def _load_config(self) -> VisionConfig:
        """加载配置"""
        try:
            max_tokens = int(os.getenv("VISION_MODEL_MAX_TOKENS", "4096"))
        except ValueError:
            logger.warning("Invalid VISION_MODEL_MAX_TOKENS value, using default 4096")
            max_tokens = 4096

        try:
            temperature = float(os.getenv("VISION_MODEL_TEMPERATURE", "0.1"))
        except ValueError:
            logger.warning("Invalid VISION_MODEL_TEMPERATURE value, using default 0.1")
            temperature = 0.1

        return VisionConfig(
            api_key=os.getenv("VISION_MODEL_API_KEY", ""),
            endpoint=os.getenv("VISION_MODEL_ENDPOINT", "https://api.openai.com/v1"),
            model=os.getenv("VISION_MODEL_NAME", "gpt-4-vision-preview"),
            max_tokens=max_tokens,
            temperature=temperature
        )
    
    def _encode_image(self, image_path: str) -> str:
        """将图片编码为base64"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"图片编码失败: {e}")
            raise
    
    async def analyze_screenshot(self, screenshot_path: str, analysis_prompt: Optional[str] = None) -> VisualAnalysisResult:
        """分析截图"""
        try:
            start_time = datetime.now()
            
            # 编码图片
            base64_image = self._encode_image(screenshot_path)
            
            # 构建分析提示
            if analysis_prompt is None:
                analysis_prompt = self._get_default_analysis_prompt()
            
            # 调用视觉模型API
            response = await self._call_vision_api(base64_image, analysis_prompt)
            
            # 解析响应
            analysis_result = self._parse_analysis_response(response)
            
            # 计算分析时间
            analysis_time = (datetime.now() - start_time).total_seconds()
            
            # 创建分析结果
            result = VisualAnalysisResult(
                screenshot_path=screenshot_path,
                elements=analysis_result.get("elements", []),
                layout_info=analysis_result.get("layout_info", {}),
                suggestions=analysis_result.get("suggestions", []),
                confidence_score=analysis_result.get("confidence_score", 0.0),
                analysis_time=analysis_time,
                model_used=self.config.model
            )
            
            logger.info(f"截图分析完成: {screenshot_path}, 置信度: {result.confidence_score}")
            return result
            
        except Exception as e:
            logger.error(f"截图分析失败: {e}")
            # 返回空的分析结果
            return VisualAnalysisResult(
                screenshot_path=screenshot_path,
                elements=[],
                layout_info={},
                suggestions=[f"分析失败: {str(e)}"],
                confidence_score=0.0,
                analysis_time=0.0,
                model_used=self.config.model
            )
    
    def _get_default_analysis_prompt(self) -> str:
        """获取默认分析提示"""
        return """
请分析这个网页截图，识别其中的UI元素并提供以下信息：

1. 识别所有可交互的UI元素（按钮、输入框、下拉菜单、链接等）
2. 分析页面布局结构
3. 提供操作建议

请以JSON格式返回结果，包含以下字段：
{
    "elements": [
        {
            "type": "元素类型(button/input/select/link等)",
            "text": "元素文本内容",
            "position": {"x": 0, "y": 0, "width": 0, "height": 0},
            "attributes": {"id": "", "class": "", "name": ""},
            "confidence": 0.9,
            "suggested_selector": "建议的CSS选择器"
        }
    ],
    "layout_info": {
        "page_type": "页面类型",
        "main_sections": ["主要区域列表"],
        "navigation": "导航信息",
        "content_area": "内容区域描述"
    },
    "suggestions": [
        "操作建议1",
        "操作建议2"
    ],
    "confidence_score": 0.85
}

请确保返回有效的JSON格式。
"""
    
    async def _call_vision_api(self, base64_image: str, prompt: str) -> Dict[str, Any]:
        """调用视觉模型API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.config.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature
            }
            
            response = await self.client.post(
                f"{self.config.endpoint}/chat/completions",
                headers=headers,
                json=payload
            )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"调用视觉API失败: {e}")
            raise
    
    def _parse_analysis_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析API响应"""
        try:
            content = response["choices"][0]["message"]["content"]
            
            # 尝试提取JSON部分
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_content = content[json_start:json_end].strip()
            elif "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_content = content[json_start:json_end]
            else:
                json_content = content
            
            # 解析JSON
            result = safe_json_loads(json_content)
            
            if result is None:
                logger.warning("无法解析API响应为JSON，使用默认结果")
                return self._get_default_result()
            
            return result
            
        except Exception as e:
            logger.error(f"解析API响应失败: {e}")
            return self._get_default_result()
    
    def _get_default_result(self) -> Dict[str, Any]:
        """获取默认分析结果"""
        return {
            "elements": [],
            "layout_info": {
                "page_type": "unknown",
                "main_sections": [],
                "navigation": "未识别",
                "content_area": "未识别"
            },
            "suggestions": ["无法自动识别页面元素，请手动指定选择器"],
            "confidence_score": 0.0
        }
    
    async def find_element_suggestions(self, screenshot_path: str, target_description: str) -> List[str]:
        """根据描述查找元素建议"""
        try:
            base64_image = self._encode_image(screenshot_path)
            
            prompt = f"""
请在这个网页截图中找到符合以下描述的元素："{target_description}"

请提供可能的CSS选择器建议，按照可能性从高到低排序。
返回JSON格式：
{{
    "suggestions": [
        "选择器1",
        "选择器2", 
        "选择器3"
    ],
    "confidence": 0.8
}}
"""
            
            response = await self._call_vision_api(base64_image, prompt)
            result = self._parse_analysis_response(response)
            
            return result.get("suggestions", [])
            
        except Exception as e:
            logger.error(f"查找元素建议失败: {e}")
            return []
    
    async def validate_element_location(self, screenshot_path: str, selector: str, expected_element_type: str) -> bool:
        """验证元素定位是否正确"""
        try:
            base64_image = self._encode_image(screenshot_path)
            
            prompt = f"""
请检查这个网页截图中，CSS选择器 "{selector}" 是否能正确定位到一个 "{expected_element_type}" 类型的元素。

返回JSON格式：
{{
    "is_valid": true/false,
    "confidence": 0.9,
    "reason": "验证结果说明"
}}
"""
            
            response = await self._call_vision_api(base64_image, prompt)
            result = self._parse_analysis_response(response)
            
            return result.get("is_valid", False)
            
        except Exception as e:
            logger.error(f"验证元素定位失败: {e}")
            return False
    
    async def get_page_layout_analysis(self, screenshot_path: str) -> Dict[str, Any]:
        """获取页面布局分析"""
        try:
            base64_image = self._encode_image(screenshot_path)
            
            prompt = """
请分析这个网页的整体布局结构，识别：
1. 页面类型（登录页、仪表板、表单页等）
2. 主要功能区域
3. 导航结构
4. 内容组织方式

返回JSON格式：
{
    "page_type": "页面类型",
    "layout_structure": {
        "header": "头部区域描述",
        "navigation": "导航区域描述", 
        "main_content": "主内容区域描述",
        "sidebar": "侧边栏描述",
        "footer": "底部区域描述"
    },
    "functional_areas": [
        "功能区域1",
        "功能区域2"
    ],
    "user_flow_suggestions": [
        "用户操作流程建议"
    ]
}
"""
            
            response = await self._call_vision_api(base64_image, prompt)
            result = self._parse_analysis_response(response)
            
            return result
            
        except Exception as e:
            logger.error(f"页面布局分析失败: {e}")
            return {}
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
