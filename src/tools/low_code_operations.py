"""
低代码平台操作工具

封装低代码平台的核心操作，包括数据建模、表单设计、页面设计等功能
基于低代码平台使用说明书实现具体操作
"""

import asyncio
import yaml
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from .playwright_automation import PlaywrightAutomation
from .visual_recognition import VisualRecognition
from ..models.low_code_models import (
    LowCodeOperation, 
    OperationType, 
    ActionType, 
    DevelopmentRequest,
    ImplementationSolution,
    VisualAnalysisResult
)
from .decorators import tool


logger = logging.getLogger(__name__)


class LowCodePlatformOperations:
    """低代码平台操作工具类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化低代码平台操作工具"""
        self.config = self._load_config(config_path)
        self.browser = PlaywrightAutomation()
        self.vision = VisualRecognition()
        self.is_authenticated = False
        self.current_module = None
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """加载低代码平台配置"""
        if config_path is None:
            config_path = "config/low_code_config.yaml"
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"加载配置失败，使用默认配置: {e}")
            return {}
    
    async def initialize(self) -> bool:
        """初始化操作环境"""
        try:
            # 启动浏览器
            if not await self.browser.start_browser():
                return False
            
            # 导航到低代码平台
            platform_url = self.config.get("LOW_CODE_PLATFORM", {}).get("base_url", "")
            if not platform_url:
                logger.error("未配置低代码平台URL")
                return False
                
            if not await self.browser.navigate_to_url(platform_url):
                return False
            
            logger.info("低代码平台操作工具初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False
    
    async def authenticate(self, username: str, password: str) -> bool:
        """登录低代码平台"""
        try:
            login_url = self.config.get("LOW_CODE_PLATFORM", {}).get("login_url", "")
            if not login_url:
                logger.error("未配置登录URL")
                return False
            
            success = await self.browser.authenticate(username, password, login_url)
            self.is_authenticated = success
            
            if success:
                logger.info("低代码平台登录成功")
                # 导航到仪表板
                dashboard_url = self.config.get("LOW_CODE_PLATFORM", {}).get("dashboard_url", "")
                if dashboard_url:
                    await self.browser.navigate_to_url(dashboard_url)
            
            return success
            
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False
    
    @tool
    async def create_data_model(self, model_name: str, fields: List[Dict[str, Any]]) -> bool:
        """创建数据模型"""
        try:
            if not self.is_authenticated:
                logger.error("未登录，无法执行操作")
                return False
            
            # 进入数据建模模块
            if not await self._enter_module("data_modeling"):
                return False
            
            # 点击创建模型按钮
            create_button_selector = self.config.get("LOW_CODE_PLATFORM", {}).get("modules", {}).get("data_modeling", {}).get("create_button", "")
            
            operation = LowCodeOperation(
                operation_type=OperationType.DATA_MODELING,
                action=ActionType.CLICK,
                target_element=create_button_selector,
                parameters={"model_name": model_name}
            )
            
            if not await self.browser.execute_operation(operation):
                return False
            
            # 填写模型名称
            await self._fill_model_name(model_name)
            
            # 添加字段
            for field in fields:
                if not await self._add_model_field(field):
                    logger.error(f"添加字段失败: {field}")
                    return False
            
            # 保存模型
            if not await self._save_model():
                return False
            
            logger.info(f"数据模型创建成功: {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"创建数据模型失败: {e}")
            return False
    
    @tool
    async def design_form(self, form_name: str, form_config: Dict[str, Any]) -> bool:
        """设计表单"""
        try:
            if not self.is_authenticated:
                logger.error("未登录，无法执行操作")
                return False
            
            # 进入表单设计模块
            if not await self._enter_module("form_design"):
                return False
            
            # 创建新表单
            if not await self._create_new_form(form_name):
                return False
            
            # 添加表单字段
            fields = form_config.get("fields", [])
            for field in fields:
                if not await self._add_form_field(field):
                    logger.error(f"添加表单字段失败: {field}")
                    return False
            
            # 配置表单属性
            if not await self._configure_form_properties(form_config):
                return False
            
            # 保存表单
            if not await self._save_form():
                return False
            
            logger.info(f"表单设计完成: {form_name}")
            return True
            
        except Exception as e:
            logger.error(f"表单设计失败: {e}")
            return False
    
    @tool
    async def design_page(self, page_name: str, page_config: Dict[str, Any]) -> bool:
        """设计页面"""
        try:
            if not self.is_authenticated:
                logger.error("未登录，无法执行操作")
                return False
            
            # 进入页面设计模块
            if not await self._enter_module("page_design"):
                return False
            
            # 创建新页面
            if not await self._create_new_page(page_name):
                return False
            
            # 添加页面组件
            components = page_config.get("components", [])
            for component in components:
                if not await self._add_page_component(component):
                    logger.error(f"添加页面组件失败: {component}")
                    return False
            
            # 配置页面布局
            if not await self._configure_page_layout(page_config):
                return False
            
            # 保存页面
            if not await self._save_page():
                return False
            
            logger.info(f"页面设计完成: {page_name}")
            return True
            
        except Exception as e:
            logger.error(f"页面设计失败: {e}")
            return False
    
    @tool
    async def create_workflow(self, workflow_name: str, workflow_config: Dict[str, Any]) -> bool:
        """创建工作流"""
        try:
            if not self.is_authenticated:
                logger.error("未登录，无法执行操作")
                return False
            
            # 进入工作流设计模块
            if not await self._enter_module("workflow_design"):
                return False
            
            # 创建新工作流
            if not await self._create_new_workflow(workflow_name):
                return False
            
            # 添加工作流节点
            nodes = workflow_config.get("nodes", [])
            for node in nodes:
                if not await self._add_workflow_node(node):
                    logger.error(f"添加工作流节点失败: {node}")
                    return False
            
            # 连接工作流节点
            connections = workflow_config.get("connections", [])
            for connection in connections:
                if not await self._connect_workflow_nodes(connection):
                    logger.error(f"连接工作流节点失败: {connection}")
                    return False
            
            # 保存工作流
            if not await self._save_workflow():
                return False
            
            logger.info(f"工作流创建完成: {workflow_name}")
            return True
            
        except Exception as e:
            logger.error(f"工作流创建失败: {e}")
            return False
    
    async def _enter_module(self, module_name: str) -> bool:
        """进入指定模块"""
        try:
            if self.current_module == module_name:
                return True
            
            module_config = self.config.get("LOW_CODE_PLATFORM", {}).get("modules", {}).get(module_name, {})
            if not module_config.get("enabled", False):
                logger.error(f"模块未启用: {module_name}")
                return False
            
            entry_selector = module_config.get("entry_selector", "")
            if not entry_selector:
                logger.error(f"未配置模块入口选择器: {module_name}")
                return False
            
            operation = LowCodeOperation(
                operation_type=OperationType.NAVIGATION,
                action=ActionType.CLICK,
                target_element=entry_selector,
                parameters={"module": module_name}
            )
            
            if await self.browser.execute_operation(operation):
                self.current_module = module_name
                logger.info(f"成功进入模块: {module_name}")
                return True
            else:
                logger.error(f"进入模块失败: {module_name}")
                return False
                
        except Exception as e:
            logger.error(f"进入模块时出错: {e}")
            return False
    
    async def _fill_model_name(self, model_name: str) -> bool:
        """填写模型名称"""
        try:
            # 使用视觉识别找到名称输入框
            screenshot_path = await self.browser.take_screenshot()
            suggestions = await self.vision.find_element_suggestions(
                screenshot_path, 
                "模型名称输入框"
            )
            
            for selector in suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.DATA_MODELING,
                    action=ActionType.FILL,
                    target_element=selector,
                    parameters={"value": model_name}
                )
                
                if await self.browser.execute_operation(operation):
                    return True
            
            logger.error("未找到模型名称输入框")
            return False
            
        except Exception as e:
            logger.error(f"填写模型名称失败: {e}")
            return False
    
    async def _add_model_field(self, field: Dict[str, Any]) -> bool:
        """添加模型字段"""
        try:
            # 点击添加字段按钮
            screenshot_path = await self.browser.take_screenshot()
            suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "添加字段按钮"
            )
            
            for selector in suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.DATA_MODELING,
                    action=ActionType.CLICK,
                    target_element=selector,
                    parameters=field
                )
                
                if await self.browser.execute_operation(operation):
                    # 填写字段信息
                    return await self._configure_field(field)
            
            logger.error("未找到添加字段按钮")
            return False
            
        except Exception as e:
            logger.error(f"添加模型字段失败: {e}")
            return False
    
    async def _configure_field(self, field: Dict[str, Any]) -> bool:
        """配置字段属性"""
        try:
            # 填写字段名称
            field_name = field.get("name", "")
            if field_name:
                # 查找字段名称输入框
                screenshot_path = await self.browser.take_screenshot()
                suggestions = await self.vision.find_element_suggestions(
                    screenshot_path,
                    "字段名称输入框"
                )
                
                for selector in suggestions:
                    operation = LowCodeOperation(
                        operation_type=OperationType.DATA_MODELING,
                        action=ActionType.FILL,
                        target_element=selector,
                        parameters={"value": field_name}
                    )
                    
                    if await self.browser.execute_operation(operation):
                        break
            
            # 选择字段类型
            field_type = field.get("type", "")
            if field_type:
                # 查找字段类型选择器
                screenshot_path = await self.browser.take_screenshot()
                suggestions = await self.vision.find_element_suggestions(
                    screenshot_path,
                    "字段类型选择器"
                )
                
                for selector in suggestions:
                    operation = LowCodeOperation(
                        operation_type=OperationType.DATA_MODELING,
                        action=ActionType.SELECT,
                        target_element=selector,
                        parameters={"option": field_type}
                    )
                    
                    if await self.browser.execute_operation(operation):
                        break
            
            # 确认字段配置
            return await self._confirm_field_config()
            
        except Exception as e:
            logger.error(f"配置字段失败: {e}")
            return False
    
    async def _confirm_field_config(self) -> bool:
        """确认字段配置"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "确认按钮"
            )
            
            for selector in suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.DATA_MODELING,
                    action=ActionType.CLICK,
                    target_element=selector,
                    parameters={}
                )
                
                if await self.browser.execute_operation(operation):
                    return True
            
            return True  # 如果没有确认按钮，假设自动保存
            
        except Exception as e:
            logger.error(f"确认字段配置失败: {e}")
            return False
    
    async def _save_model(self) -> bool:
        """保存数据模型"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "保存按钮"
            )
            
            for selector in suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.DATA_MODELING,
                    action=ActionType.CLICK,
                    target_element=selector,
                    parameters={}
                )
                
                if await self.browser.execute_operation(operation):
                    # 等待保存完成
                    await asyncio.sleep(2)
                    return True
            
            logger.error("未找到保存按钮")
            return False
            
        except Exception as e:
            logger.error(f"保存模型失败: {e}")
            return False
    
    # 表单设计相关方法
    async def _create_new_form(self, form_name: str) -> bool:
        """创建新表单"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "创建表单按钮"
            )

            for selector in suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.FORM_DESIGN,
                    action=ActionType.CLICK,
                    target_element=selector,
                    parameters={"form_name": form_name}
                )

                if await self.browser.execute_operation(operation):
                    # 填写表单名称
                    return await self._fill_form_name(form_name)

            logger.error("未找到创建表单按钮")
            return False

        except Exception as e:
            logger.error(f"创建新表单失败: {e}")
            return False

    async def _fill_form_name(self, form_name: str) -> bool:
        """填写表单名称"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "表单名称输入框"
            )

            for selector in suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.FORM_DESIGN,
                    action=ActionType.FILL,
                    target_element=selector,
                    parameters={"value": form_name}
                )

                if await self.browser.execute_operation(operation):
                    return True

            return True  # 如果没有名称输入框，可能是自动生成

        except Exception as e:
            logger.error(f"填写表单名称失败: {e}")
            return False

    async def _add_form_field(self, field: Dict[str, Any]) -> bool:
        """添加表单字段"""
        try:
            field_type = field.get("type", "input")
            field_label = field.get("label", "")

            # 从组件库拖拽字段到表单
            screenshot_path = await self.browser.take_screenshot()

            # 查找对应类型的组件
            component_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                f"{field_type}组件"
            )

            # 查找表单画布
            canvas_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "表单画布"
            )

            if component_suggestions and canvas_suggestions:
                # 执行拖拽操作
                drag_operation = LowCodeOperation(
                    operation_type=OperationType.FORM_DESIGN,
                    action=ActionType.DRAG_DROP,
                    target_element=component_suggestions[0],
                    parameters={
                        "source": component_suggestions[0],
                        "target": canvas_suggestions[0],
                        "field_config": field
                    }
                )

                if await self.browser.execute_operation(drag_operation):
                    # 配置字段属性
                    return await self._configure_form_field(field)

            logger.error(f"添加表单字段失败: {field}")
            return False

        except Exception as e:
            logger.error(f"添加表单字段失败: {e}")
            return False

    async def _configure_form_field(self, field: Dict[str, Any]) -> bool:
        """配置表单字段属性"""
        try:
            # 双击字段打开属性配置
            screenshot_path = await self.browser.take_screenshot()
            field_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "刚添加的表单字段"
            )

            if field_suggestions:
                # 双击打开属性面板
                double_click_operation = LowCodeOperation(
                    operation_type=OperationType.FORM_DESIGN,
                    action=ActionType.CLICK,
                    target_element=field_suggestions[0],
                    parameters={"click_count": 2}
                )

                await self.browser.execute_operation(double_click_operation)

                # 配置字段属性
                await self._set_field_properties(field)

                # 确认配置
                return await self._confirm_field_properties()

            return True

        except Exception as e:
            logger.error(f"配置表单字段失败: {e}")
            return False

    async def _set_field_properties(self, field: Dict[str, Any]) -> bool:
        """设置字段属性"""
        try:
            properties = field.get("properties", {})

            for prop_name, prop_value in properties.items():
                # 查找属性输入框
                screenshot_path = await self.browser.take_screenshot()
                prop_suggestions = await self.vision.find_element_suggestions(
                    screenshot_path,
                    f"{prop_name}属性输入框"
                )

                if prop_suggestions:
                    operation = LowCodeOperation(
                        operation_type=OperationType.FORM_DESIGN,
                        action=ActionType.FILL,
                        target_element=prop_suggestions[0],
                        parameters={"value": str(prop_value)}
                    )

                    await self.browser.execute_operation(operation)

            return True

        except Exception as e:
            logger.error(f"设置字段属性失败: {e}")
            return False

    async def _confirm_field_properties(self) -> bool:
        """确认字段属性配置"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            confirm_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "确认按钮"
            )

            if confirm_suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.FORM_DESIGN,
                    action=ActionType.CLICK,
                    target_element=confirm_suggestions[0],
                    parameters={}
                )

                return await self.browser.execute_operation(operation)

            return True  # 如果没有确认按钮，假设自动保存

        except Exception as e:
            logger.error(f"确认字段属性失败: {e}")
            return False

    async def _configure_form_properties(self, form_config: Dict[str, Any]) -> bool:
        """配置表单属性"""
        try:
            # 打开表单属性面板
            screenshot_path = await self.browser.take_screenshot()
            properties_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "表单属性按钮"
            )

            if properties_suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.FORM_DESIGN,
                    action=ActionType.CLICK,
                    target_element=properties_suggestions[0],
                    parameters={}
                )

                await self.browser.execute_operation(operation)

                # 配置表单属性
                properties = form_config.get("properties", {})
                for prop_name, prop_value in properties.items():
                    await self._set_form_property(prop_name, prop_value)

            return True

        except Exception as e:
            logger.error(f"配置表单属性失败: {e}")
            return False

    async def _set_form_property(self, prop_name: str, prop_value: Any) -> bool:
        """设置表单属性"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            prop_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                f"{prop_name}属性输入框"
            )

            if prop_suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.FORM_DESIGN,
                    action=ActionType.FILL,
                    target_element=prop_suggestions[0],
                    parameters={"value": str(prop_value)}
                )

                return await self.browser.execute_operation(operation)

            return True

        except Exception as e:
            logger.error(f"设置表单属性失败: {e}")
            return False

    async def _save_form(self) -> bool:
        """保存表单"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            save_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "保存表单按钮"
            )

            for selector in save_suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.FORM_DESIGN,
                    action=ActionType.CLICK,
                    target_element=selector,
                    parameters={}
                )

                if await self.browser.execute_operation(operation):
                    await asyncio.sleep(2)  # 等待保存完成
                    return True

            logger.error("未找到保存表单按钮")
            return False

        except Exception as e:
            logger.error(f"保存表单失败: {e}")
            return False

    async def close(self):
        """关闭操作工具"""
        try:
            await self.browser.close_browser()
            await self.vision.close()
            logger.info("低代码平台操作工具已关闭")
        except Exception as e:
            logger.error(f"关闭操作工具时出错: {e}")
