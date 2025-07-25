"""
低代码平台高级操作工具

包含页面设计、工作流设计等高级功能的实现
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from .playwright_automation import PlaywrightAutomation
from .visual_recognition import VisualRecognition
from ..models.low_code_models import (
    LowCodeOperation, 
    OperationType, 
    ActionType
)


logger = logging.getLogger(__name__)


class LowCodeAdvancedOperations:
    """低代码平台高级操作工具类"""
    
    def __init__(self, browser: PlaywrightAutomation, vision: VisualRecognition):
        """初始化高级操作工具"""
        self.browser = browser
        self.vision = vision
    
    # 页面设计相关方法
    async def _create_new_page(self, page_name: str) -> bool:
        """创建新页面"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "创建页面按钮"
            )
            
            for selector in suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.PAGE_DESIGN,
                    action=ActionType.CLICK,
                    target_element=selector,
                    parameters={"page_name": page_name}
                )
                
                if await self.browser.execute_operation(operation):
                    return await self._fill_page_name(page_name)
            
            logger.error("未找到创建页面按钮")
            return False
            
        except Exception as e:
            logger.error(f"创建新页面失败: {e}")
            return False
    
    async def _fill_page_name(self, page_name: str) -> bool:
        """填写页面名称"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "页面名称输入框"
            )
            
            for selector in suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.PAGE_DESIGN,
                    action=ActionType.FILL,
                    target_element=selector,
                    parameters={"value": page_name}
                )
                
                if await self.browser.execute_operation(operation):
                    return True
            
            return True  # 如果没有名称输入框，可能是自动生成
            
        except Exception as e:
            logger.error(f"填写页面名称失败: {e}")
            return False
    
    async def _add_page_component(self, component: Dict[str, Any]) -> bool:
        """添加页面组件"""
        try:
            component_type = component.get("type", "")
            component_config = component.get("config", {})
            
            # 从组件库拖拽组件到页面
            screenshot_path = await self.browser.take_screenshot()
            
            # 查找对应类型的组件
            component_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                f"{component_type}组件"
            )
            
            # 查找页面画布
            canvas_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "页面画布"
            )
            
            if component_suggestions and canvas_suggestions:
                # 执行拖拽操作
                drag_operation = LowCodeOperation(
                    operation_type=OperationType.PAGE_DESIGN,
                    action=ActionType.DRAG_DROP,
                    target_element=component_suggestions[0],
                    parameters={
                        "source": component_suggestions[0],
                        "target": canvas_suggestions[0],
                        "component_config": component_config
                    }
                )
                
                if await self.browser.execute_operation(drag_operation):
                    # 配置组件属性
                    return await self._configure_page_component(component)
            
            logger.error(f"添加页面组件失败: {component}")
            return False
            
        except Exception as e:
            logger.error(f"添加页面组件失败: {e}")
            return False
    
    async def _configure_page_component(self, component: Dict[str, Any]) -> bool:
        """配置页面组件"""
        try:
            # 选中刚添加的组件
            screenshot_path = await self.browser.take_screenshot()
            component_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "刚添加的页面组件"
            )
            
            if component_suggestions:
                # 点击选中组件
                select_operation = LowCodeOperation(
                    operation_type=OperationType.PAGE_DESIGN,
                    action=ActionType.CLICK,
                    target_element=component_suggestions[0],
                    parameters={}
                )
                
                await self.browser.execute_operation(select_operation)
                
                # 配置组件属性
                config = component.get("config", {})
                for prop_name, prop_value in config.items():
                    await self._set_component_property(prop_name, prop_value)
                
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"配置页面组件失败: {e}")
            return False
    
    async def _set_component_property(self, prop_name: str, prop_value: Any) -> bool:
        """设置组件属性"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            prop_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                f"{prop_name}属性输入框"
            )
            
            if prop_suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.PAGE_DESIGN,
                    action=ActionType.FILL,
                    target_element=prop_suggestions[0],
                    parameters={"value": str(prop_value)}
                )
                
                return await self.browser.execute_operation(operation)
            
            return True
            
        except Exception as e:
            logger.error(f"设置组件属性失败: {e}")
            return False
    
    async def _configure_page_layout(self, page_config: Dict[str, Any]) -> bool:
        """配置页面布局"""
        try:
            layout_config = page_config.get("layout", {})
            
            # 设置页面布局类型
            layout_type = layout_config.get("type", "")
            if layout_type:
                await self._set_page_layout_type(layout_type)
            
            # 配置布局属性
            layout_properties = layout_config.get("properties", {})
            for prop_name, prop_value in layout_properties.items():
                await self._set_layout_property(prop_name, prop_value)
            
            return True
            
        except Exception as e:
            logger.error(f"配置页面布局失败: {e}")
            return False
    
    async def _set_page_layout_type(self, layout_type: str) -> bool:
        """设置页面布局类型"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            layout_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "页面布局选择器"
            )
            
            if layout_suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.PAGE_DESIGN,
                    action=ActionType.SELECT,
                    target_element=layout_suggestions[0],
                    parameters={"option": layout_type}
                )
                
                return await self.browser.execute_operation(operation)
            
            return True
            
        except Exception as e:
            logger.error(f"设置页面布局类型失败: {e}")
            return False
    
    async def _set_layout_property(self, prop_name: str, prop_value: Any) -> bool:
        """设置布局属性"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            prop_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                f"{prop_name}布局属性"
            )
            
            if prop_suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.PAGE_DESIGN,
                    action=ActionType.FILL,
                    target_element=prop_suggestions[0],
                    parameters={"value": str(prop_value)}
                )
                
                return await self.browser.execute_operation(operation)
            
            return True
            
        except Exception as e:
            logger.error(f"设置布局属性失败: {e}")
            return False
    
    async def _save_page(self) -> bool:
        """保存页面"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            save_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "保存页面按钮"
            )
            
            for selector in save_suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.PAGE_DESIGN,
                    action=ActionType.CLICK,
                    target_element=selector,
                    parameters={}
                )
                
                if await self.browser.execute_operation(operation):
                    await asyncio.sleep(2)  # 等待保存完成
                    return True
            
            logger.error("未找到保存页面按钮")
            return False
            
        except Exception as e:
            logger.error(f"保存页面失败: {e}")
            return False
    
    # 工作流设计相关方法
    async def _create_new_workflow(self, workflow_name: str) -> bool:
        """创建新工作流"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "创建工作流按钮"
            )
            
            for selector in suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.WORKFLOW_DESIGN,
                    action=ActionType.CLICK,
                    target_element=selector,
                    parameters={"workflow_name": workflow_name}
                )
                
                if await self.browser.execute_operation(operation):
                    return await self._fill_workflow_name(workflow_name)
            
            logger.error("未找到创建工作流按钮")
            return False
            
        except Exception as e:
            logger.error(f"创建新工作流失败: {e}")
            return False
    
    async def _fill_workflow_name(self, workflow_name: str) -> bool:
        """填写工作流名称"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "工作流名称输入框"
            )
            
            for selector in suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.WORKFLOW_DESIGN,
                    action=ActionType.FILL,
                    target_element=selector,
                    parameters={"value": workflow_name}
                )
                
                if await self.browser.execute_operation(operation):
                    return True
            
            return True  # 如果没有名称输入框，可能是自动生成
            
        except Exception as e:
            logger.error(f"填写工作流名称失败: {e}")
            return False
    
    async def _add_workflow_node(self, node: Dict[str, Any]) -> bool:
        """添加工作流节点"""
        try:
            node_type = node.get("type", "")
            node_config = node.get("config", {})
            
            # 从节点库拖拽节点到工作流画布
            screenshot_path = await self.browser.take_screenshot()
            
            # 查找对应类型的节点
            node_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                f"{node_type}节点"
            )
            
            # 查找工作流画布
            canvas_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "工作流画布"
            )
            
            if node_suggestions and canvas_suggestions:
                # 执行拖拽操作
                drag_operation = LowCodeOperation(
                    operation_type=OperationType.WORKFLOW_DESIGN,
                    action=ActionType.DRAG_DROP,
                    target_element=node_suggestions[0],
                    parameters={
                        "source": node_suggestions[0],
                        "target": canvas_suggestions[0],
                        "node_config": node_config
                    }
                )
                
                if await self.browser.execute_operation(drag_operation):
                    # 配置节点属性
                    return await self._configure_workflow_node(node)
            
            logger.error(f"添加工作流节点失败: {node}")
            return False
            
        except Exception as e:
            logger.error(f"添加工作流节点失败: {e}")
            return False
    
    async def _configure_workflow_node(self, node: Dict[str, Any]) -> bool:
        """配置工作流节点"""
        try:
            # 双击节点打开配置面板
            screenshot_path = await self.browser.take_screenshot()
            node_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "刚添加的工作流节点"
            )
            
            if node_suggestions:
                # 双击打开配置面板
                double_click_operation = LowCodeOperation(
                    operation_type=OperationType.WORKFLOW_DESIGN,
                    action=ActionType.CLICK,
                    target_element=node_suggestions[0],
                    parameters={"click_count": 2}
                )
                
                await self.browser.execute_operation(double_click_operation)
                
                # 配置节点属性
                config = node.get("config", {})
                for prop_name, prop_value in config.items():
                    await self._set_node_property(prop_name, prop_value)
                
                # 确认配置
                return await self._confirm_node_config()
            
            return True
            
        except Exception as e:
            logger.error(f"配置工作流节点失败: {e}")
            return False
    
    async def _set_node_property(self, prop_name: str, prop_value: Any) -> bool:
        """设置节点属性"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            prop_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                f"{prop_name}节点属性"
            )
            
            if prop_suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.WORKFLOW_DESIGN,
                    action=ActionType.FILL,
                    target_element=prop_suggestions[0],
                    parameters={"value": str(prop_value)}
                )
                
                return await self.browser.execute_operation(operation)
            
            return True
            
        except Exception as e:
            logger.error(f"设置节点属性失败: {e}")
            return False
    
    async def _confirm_node_config(self) -> bool:
        """确认节点配置"""
        try:
            screenshot_path = await self.browser.take_screenshot()
            confirm_suggestions = await self.vision.find_element_suggestions(
                screenshot_path,
                "确认节点配置按钮"
            )
            
            if confirm_suggestions:
                operation = LowCodeOperation(
                    operation_type=OperationType.WORKFLOW_DESIGN,
                    action=ActionType.CLICK,
                    target_element=confirm_suggestions[0],
                    parameters={}
                )
                
                return await self.browser.execute_operation(operation)
            
            return True  # 如果没有确认按钮，假设自动保存
            
        except Exception as e:
            logger.error(f"确认节点配置失败: {e}")
            return False
