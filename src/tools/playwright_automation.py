"""
Playwright浏览器自动化工具

基于Playwright实现的低代码平台浏览器自动化操作工具
支持页面导航、元素定位、操作执行等功能
"""

import asyncio
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import logging

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
from pydantic import BaseModel

from ..models.low_code_models import LowCodeOperation, ActionType, OperationType, SessionInfo, OperationCheckpoint
from ..utils.json_utils import safe_json_loads


logger = logging.getLogger(__name__)


class BrowserConfig(BaseModel):
    """浏览器配置模型"""
    browser_type: str = "chromium"
    headless: bool = False
    slow_mo: int = 100
    viewport_width: int = 1920
    viewport_height: int = 1080
    timeout: int = 30000
    user_agent: Optional[str] = None


class PlaywrightAutomation:
    """Playwright浏览器自动化工具类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化浏览器自动化工具"""
        self.config = self._load_config(config_path)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.session_info: Optional[SessionInfo] = None
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        
    def _load_config(self, config_path: Optional[str] = None) -> BrowserConfig:
        """加载浏览器配置"""
        if config_path is None:
            config_path = "config/browser_config.yaml"
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                
            browser_config = config_data.get('BROWSER_LAUNCH', {})
            page_config = config_data.get('PAGE_CONFIG', {})
            
            return BrowserConfig(
                browser_type=browser_config.get('browser_type', 'chromium'),
                headless=browser_config.get('launch_options', {}).get('headless', False),
                slow_mo=browser_config.get('launch_options', {}).get('slow_mo', 100),
                viewport_width=page_config.get('viewport', {}).get('width', 1920),
                viewport_height=page_config.get('viewport', {}).get('height', 1080),
                timeout=page_config.get('timeouts', {}).get('default_timeout', 30000),
                user_agent=page_config.get('user_agent')
            )
        except Exception as e:
            logger.warning(f"加载配置失败，使用默认配置: {e}")
            return BrowserConfig()
    
    async def start_browser(self) -> bool:
        """启动浏览器"""
        try:
            self.playwright = await async_playwright().start()
            
            # 选择浏览器类型
            if self.config.browser_type == "firefox":
                browser_type = self.playwright.firefox
            elif self.config.browser_type == "webkit":
                browser_type = self.playwright.webkit
            else:
                browser_type = self.playwright.chromium
            
            # 启动浏览器
            self.browser = await browser_type.launch(
                headless=self.config.headless,
                slow_mo=self.config.slow_mo,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    f"--window-size={self.config.viewport_width},{self.config.viewport_height}"
                ]
            )
            
            # 创建浏览器上下文
            self.context = await self.browser.new_context(
                viewport={
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height
                },
                user_agent=self.config.user_agent
            )
            
            # 创建页面
            self.page = await self.context.new_page()
            
            # 设置默认超时
            self.page.set_default_timeout(self.config.timeout)
            
            logger.info("浏览器启动成功")
            return True
            
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            return False
    
    async def close_browser(self) -> None:
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
                
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器时出错: {e}")
    
    async def navigate_to_url(self, url: str, wait_until: str = "networkidle") -> bool:
        """导航到指定URL"""
        try:
            if not self.page:
                raise Exception("浏览器页面未初始化")
                
            await self.page.goto(url, wait_until=wait_until)
            logger.info(f"成功导航到: {url}")
            return True
            
        except Exception as e:
            logger.error(f"导航失败: {e}")
            return False
    
    async def take_screenshot(self, filename: Optional[str] = None, full_page: bool = True) -> str:
        """截图"""
        try:
            if not self.page:
                raise Exception("浏览器页面未初始化")
                
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                filename = f"screenshot_{timestamp}.png"
                
            screenshot_path = self.screenshots_dir / filename
            await self.page.screenshot(path=str(screenshot_path), full_page=full_page)
            
            logger.info(f"截图已保存: {screenshot_path}")
            return str(screenshot_path)
            
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return ""
    
    async def wait_for_element(self, selector: str, timeout: Optional[int] = None, state: str = "visible") -> bool:
        """等待元素出现"""
        try:
            if not self.page:
                raise Exception("浏览器页面未初始化")
                
            timeout = timeout or self.config.timeout
            await self.page.wait_for_selector(selector, timeout=timeout, state=state)
            return True
            
        except PlaywrightTimeoutError:
            logger.warning(f"等待元素超时: {selector}")
            return False
        except Exception as e:
            logger.error(f"等待元素失败: {e}")
            return False
    
    async def execute_operation(self, operation: LowCodeOperation) -> bool:
        """执行低代码操作"""
        try:
            if not self.page:
                raise Exception("浏览器页面未初始化")
            
            start_time = datetime.now()
            
            # 操作前截图
            if operation.screenshot_before is None:
                operation.screenshot_before = await self.take_screenshot(
                    f"before_{operation.operation_id}.png"
                )
            
            # 等待目标元素
            if not await self.wait_for_element(operation.target_element, operation.timeout):
                operation.error_message = f"目标元素未找到: {operation.target_element}"
                return False
            
            # 执行具体操作
            success = await self._execute_action(operation)
            
            # 操作后截图
            if success:
                operation.screenshot_after = await self.take_screenshot(
                    f"after_{operation.operation_id}.png"
                )
            
            # 记录执行时间
            operation.execution_time = (datetime.now() - start_time).total_seconds()
            operation.success = success
            
            if success:
                logger.info(f"操作执行成功: {operation.operation_type} - {operation.action}")
            else:
                logger.error(f"操作执行失败: {operation.error_message}")
                
            return success
            
        except Exception as e:
            operation.error_message = str(e)
            operation.success = False
            logger.error(f"执行操作时出错: {e}")
            return False
    
    async def _execute_action(self, operation: LowCodeOperation) -> bool:
        """执行具体的操作动作"""
        try:
            element = self.page.locator(operation.target_element)
            
            if operation.action == ActionType.CLICK:
                await element.click(timeout=operation.timeout)
                
            elif operation.action == ActionType.FILL:
                value = operation.parameters.get("value", "")
                await element.fill(value, timeout=operation.timeout)
                
            elif operation.action == ActionType.SELECT:
                option = operation.parameters.get("option", "")
                await element.select_option(option, timeout=operation.timeout)
                
            elif operation.action == ActionType.HOVER:
                await element.hover(timeout=operation.timeout)
                
            elif operation.action == ActionType.WAIT:
                wait_time = operation.parameters.get("time", 1000)
                await asyncio.sleep(wait_time / 1000)
                
            elif operation.action == ActionType.SCREENSHOT:
                await self.take_screenshot()
                
            else:
                operation.error_message = f"不支持的操作类型: {operation.action}"
                return False
            
            # 等待操作完成
            await self.page.wait_for_load_state("networkidle", timeout=5000)
            return True
            
        except PlaywrightTimeoutError:
            operation.error_message = f"操作超时: {operation.action}"
            return False
        except Exception as e:
            operation.error_message = f"操作执行失败: {str(e)}"
            return False
    
    async def create_checkpoint(self, checkpoint_id: str, solution_id: str, operation_index: int) -> OperationCheckpoint:
        """创建操作检查点"""
        try:
            # 获取当前页面状态
            state_snapshot = {
                "url": self.page.url if self.page else "",
                "title": await self.page.title() if self.page else "",
                "timestamp": datetime.now().isoformat(),
                "viewport": {
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height
                }
            }
            
            # 截图作为检查点
            screenshot_path = await self.take_screenshot(f"checkpoint_{checkpoint_id}.png")
            
            checkpoint = OperationCheckpoint(
                checkpoint_id=checkpoint_id,
                solution_id=solution_id,
                operation_index=operation_index,
                state_snapshot=state_snapshot,
                screenshot_path=screenshot_path
            )
            
            logger.info(f"检查点已创建: {checkpoint_id}")
            return checkpoint
            
        except Exception as e:
            logger.error(f"创建检查点失败: {e}")
            raise
    
    async def authenticate(self, username: str, password: str, login_url: str) -> bool:
        """登录认证"""
        try:
            # 导航到登录页面
            if not await self.navigate_to_url(login_url):
                return False
            
            # 等待登录表单
            if not await self.wait_for_element("input[name='username'], input[type='email']"):
                logger.error("未找到用户名输入框")
                return False
            
            # 填写用户名
            await self.page.fill("input[name='username'], input[type='email']", username)
            
            # 填写密码
            await self.page.fill("input[name='password'], input[type='password']", password)
            
            # 点击登录按钮
            await self.page.click("button[type='submit'], input[type='submit'], .login-button")
            
            # 等待登录完成
            await self.page.wait_for_load_state("networkidle")
            
            # 检查是否登录成功（通过URL变化或特定元素判断）
            current_url = self.page.url
            if "login" not in current_url.lower() or await self.page.locator(".user-menu, .dashboard").count() > 0:
                logger.info("登录成功")
                return True
            else:
                logger.error("登录失败")
                return False
                
        except Exception as e:
            logger.error(f"登录过程中出错: {e}")
            return False
