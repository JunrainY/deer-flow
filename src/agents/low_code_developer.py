"""
低代码开发智能体

基于DeerFlow架构的低代码平台自动化开发智能体
集成浏览器自动化、视觉识别和低代码平台操作功能
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import os

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from ..models.low_code_models import (
    DevelopmentRequest,
    ImplementationSolution,
    LowCodeOperation,
    OperationType,
    ActionType,
    RewardDecision,
    SessionInfo,
    OperationCheckpoint,
    ValidationResult
)
from ..tools.low_code_operations import LowCodePlatformOperations
from ..tools.visual_recognition import VisualRecognition
from ..llms.llm import get_llm
from ..config.configuration import get_config


logger = logging.getLogger(__name__)


class LowCodeDeveloperState(BaseModel):
    """低代码开发智能体状态"""
    request: Optional[DevelopmentRequest] = None
    solution: Optional[ImplementationSolution] = None
    current_operation_index: int = 0
    session_info: Optional[SessionInfo] = None
    error_count: int = 0
    max_errors: int = 5
    checkpoints: List[OperationCheckpoint] = Field(default_factory=list)
    messages: List[Any] = Field(default_factory=list)
    is_authenticated: bool = False
    current_module: Optional[str] = None


class LowCodeDeveloperAgent:
    """低代码开发智能体类"""
    
    def __init__(self):
        """初始化低代码开发智能体"""
        self.config = get_config()
        self.llm = get_llm()
        self.operations = LowCodePlatformOperations()
        self.vision = VisualRecognition()
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """构建智能体工作流图"""
        graph = StateGraph(LowCodeDeveloperState)
        
        # 添加节点
        graph.add_node("analyze_request", self._analyze_request)
        graph.add_node("plan_implementation", self._plan_implementation)
        graph.add_node("authenticate", self._authenticate)
        graph.add_node("execute_operations", self._execute_operations)
        graph.add_node("validate_result", self._validate_result)
        graph.add_node("handle_error", self._handle_error)
        graph.add_node("finalize_solution", self._finalize_solution)
        
        # 设置入口点
        graph.set_entry_point("analyze_request")
        
        # 添加边
        graph.add_edge("analyze_request", "plan_implementation")
        graph.add_edge("plan_implementation", "authenticate")
        graph.add_conditional_edges(
            "authenticate",
            self._should_continue_after_auth,
            {
                "continue": "execute_operations",
                "retry": "authenticate",
                "error": "handle_error"
            }
        )
        graph.add_conditional_edges(
            "execute_operations",
            self._should_continue_execution,
            {
                "continue": "execute_operations",
                "validate": "validate_result",
                "error": "handle_error"
            }
        )
        graph.add_conditional_edges(
            "validate_result",
            self._should_continue_after_validation,
            {
                "success": "finalize_solution",
                "retry": "execute_operations",
                "error": "handle_error"
            }
        )
        graph.add_edge("handle_error", "finalize_solution")
        graph.add_edge("finalize_solution", END)
        
        return graph.compile()
    
    async def develop(self, request: DevelopmentRequest) -> ImplementationSolution:
        """开发低代码功能"""
        try:
            # 初始化状态
            initial_state = LowCodeDeveloperState(
                request=request,
                solution=ImplementationSolution(
                    request_id=request.request_id,
                    title=f"实现方案: {request.title}",
                    description=f"基于需求自动生成的实现方案",
                    operations=[],
                    developer_agent="low_code_developer"
                )
            )
            
            # 执行工作流
            final_state = await self.graph.ainvoke(initial_state)

            # 安全地访问solution属性
            if hasattr(final_state, 'solution') and final_state.solution:
                return final_state.solution
            elif hasattr(final_state, 'current_solution') and final_state.current_solution:
                return final_state.current_solution
            else:
                logger.error("工作流未返回有效方案")
                return ImplementationSolution(
                    request_id=request.request_id,
                    title=f"失败方案: {request.title}",
                    description="智能体执行失败",
                    operations=[],
                    reward_decision=RewardDecision.REJECTED
                )
            
        except Exception as e:
            logger.error(f"开发过程中出错: {e}")
            # 返回失败的方案
            return ImplementationSolution(
                request_id=request.request_id,
                title=f"实现方案: {request.title}",
                description=f"开发失败: {str(e)}",
                operations=[],
                developer_agent="low_code_developer",
                reward_decision=RewardDecision.REJECTED
            )
    
    async def _analyze_request(self, state: LowCodeDeveloperState) -> LowCodeDeveloperState:
        """分析开发需求"""
        try:
            logger.info(f"分析开发需求: {state.request.title}")
            
            # 使用LLM分析需求
            analysis_prompt = ChatPromptTemplate.from_template("""
你是一个低代码平台开发专家。请分析以下开发需求，并提供详细的分析结果。

需求标题: {title}
需求描述: {description}
具体要求: {requirements}
优先级: {priority}

请分析：
1. 需求的复杂度和可行性
2. 需要使用的低代码平台功能模块
3. 实现的大致步骤
4. 可能遇到的挑战和风险

请以JSON格式返回分析结果：
{{
    "complexity": "简单/中等/复杂",
    "feasibility": "高/中/低",
    "required_modules": ["模块1", "模块2"],
    "implementation_steps": ["步骤1", "步骤2"],
    "challenges": ["挑战1", "挑战2"],
    "estimated_time": "预估时间(分钟)"
}}
""")
            
            response = await self.llm.ainvoke(
                analysis_prompt.format_messages(
                    title=state.request.title,
                    description=state.request.description,
                    requirements=", ".join(state.request.requirements),
                    priority=state.request.priority.name
                )
            )
            
            # 解析分析结果
            analysis_result = self._parse_analysis_result(response.content)
            
            # 更新方案描述
            state.solution.description = f"需求分析完成。复杂度: {analysis_result.get('complexity', '未知')}, 可行性: {analysis_result.get('feasibility', '未知')}"
            state.solution.metadata["analysis"] = analysis_result
            
            logger.info(f"需求分析完成: {analysis_result}")
            return state
            
        except Exception as e:
            logger.error(f"分析需求失败: {e}")
            state.error_count += 1
            return state
    
    async def _plan_implementation(self, state: LowCodeDeveloperState) -> LowCodeDeveloperState:
        """规划实现方案"""
        try:
            logger.info("规划实现方案")
            
            analysis = state.solution.metadata.get("analysis", {})
            required_modules = analysis.get("required_modules", [])
            
            # 使用LLM规划具体操作
            planning_prompt = ChatPromptTemplate.from_template("""
基于需求分析结果，请规划详细的低代码平台操作步骤。

需求: {description}
要求: {requirements}
需要的模块: {modules}

请规划具体的操作序列，每个操作包含：
- 操作类型 (data_modeling/form_design/page_design/workflow_design等)
- 操作动作 (click/fill/select/drag_drop等)
- 目标元素描述
- 操作参数

请以JSON格式返回操作计划：
{{
    "operations": [
        {{
            "operation_type": "data_modeling",
            "action": "click",
            "target_description": "创建数据模型按钮",
            "parameters": {{"model_name": "用户信息"}},
            "expected_result": "打开数据模型创建界面"
        }}
    ]
}}
""")
            
            response = await self.llm.ainvoke(
                planning_prompt.format_messages(
                    description=state.request.description,
                    requirements=", ".join(state.request.requirements),
                    modules=", ".join(required_modules)
                )
            )
            
            # 解析操作计划
            plan_result = self._parse_plan_result(response.content)
            operations = plan_result.get("operations", [])
            
            # 创建操作对象
            for op_data in operations:
                operation = LowCodeOperation(
                    operation_type=OperationType(op_data.get("operation_type", "navigation")),
                    action=ActionType(op_data.get("action", "click")),
                    target_element="",  # 将在执行时通过视觉识别确定
                    parameters=op_data.get("parameters", {}),
                    expected_result=op_data.get("expected_result", "")
                )
                operation.parameters["target_description"] = op_data.get("target_description", "")
                state.solution.add_operation(operation)
            
            logger.info(f"实现方案规划完成，共{len(state.solution.operations)}个操作")
            return state
            
        except Exception as e:
            logger.error(f"规划实现方案失败: {e}")
            state.error_count += 1
            return state
    
    async def _authenticate(self, state: LowCodeDeveloperState) -> LowCodeDeveloperState:
        """认证登录"""
        try:
            if state.is_authenticated:
                return state
                
            logger.info("开始认证登录")
            
            # 初始化操作工具
            if not await self.operations.initialize():
                raise Exception("初始化操作工具失败")
            
            # 获取登录凭据
            username = os.getenv("LOW_CODE_USERNAME", "")
            password = os.getenv("LOW_CODE_PASSWORD", "")
            
            if not username or not password:
                raise Exception("未配置登录凭据")
            
            # 执行登录
            if await self.operations.authenticate(username, password):
                state.is_authenticated = True
                state.session_info = SessionInfo(
                    platform_url=os.getenv("LOW_CODE_PLATFORM_URL", ""),
                    is_authenticated=True
                )
                logger.info("登录成功")
            else:
                raise Exception("登录失败")
            
            return state
            
        except Exception as e:
            logger.error(f"认证失败: {e}")
            state.error_count += 1
            return state
    
    async def _execute_operations(self, state: LowCodeDeveloperState) -> LowCodeDeveloperState:
        """执行操作序列"""
        try:
            if state.current_operation_index >= len(state.solution.operations):
                logger.info("所有操作执行完成")
                return state
            
            current_op = state.solution.operations[state.current_operation_index]
            logger.info(f"执行操作 {state.current_operation_index + 1}/{len(state.solution.operations)}: {current_op.operation_type}")
            
            # 创建检查点
            checkpoint = await self.operations.browser.create_checkpoint(
                f"checkpoint_{state.current_operation_index}",
                state.solution.solution_id,
                state.current_operation_index
            )
            state.checkpoints.append(checkpoint)
            
            # 使用视觉识别确定目标元素
            target_description = current_op.parameters.get("target_description", "")
            if target_description and not current_op.target_element:
                screenshot_path = await self.operations.browser.take_screenshot()
                suggestions = await self.vision.find_element_suggestions(
                    screenshot_path,
                    target_description
                )
                if suggestions:
                    current_op.target_element = suggestions[0]
                else:
                    logger.warning(f"未找到目标元素: {target_description}")
                    current_op.target_element = f"[data-testid='{target_description.replace(' ', '-').lower()}']"
            
            # 执行操作
            success = await self.operations.browser.execute_operation(current_op)
            
            if success:
                logger.info(f"操作执行成功: {current_op.operation_type}")
                state.current_operation_index += 1
            else:
                logger.error(f"操作执行失败: {current_op.error_message}")
                state.error_count += 1
            
            return state
            
        except Exception as e:
            logger.error(f"执行操作失败: {e}")
            state.error_count += 1
            return state
    
    def _parse_analysis_result(self, content: str) -> Dict[str, Any]:
        """解析分析结果"""
        try:
            import json
            # 尝试提取JSON部分
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                json_content = content[start:end].strip()
            elif "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_content = content[start:end]
            else:
                json_content = content
            
            return json.loads(json_content)
        except Exception as e:
            logger.warning(f"解析分析结果失败: {e}")
            return {
                "complexity": "中等",
                "feasibility": "中",
                "required_modules": ["form_design"],
                "implementation_steps": ["创建表单", "配置字段", "保存表单"],
                "challenges": ["元素定位可能不准确"],
                "estimated_time": "30"
            }
    
    def _parse_plan_result(self, content: str) -> Dict[str, Any]:
        """解析规划结果"""
        try:
            import json
            # 尝试提取JSON部分
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                json_content = content[start:end].strip()
            elif "{" in content and "}" in content:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_content = content[start:end]
            else:
                json_content = content
            
            return json.loads(json_content)
        except Exception as e:
            logger.warning(f"解析规划结果失败: {e}")
            return {
                "operations": [
                    {
                        "operation_type": "form_design",
                        "action": "click",
                        "target_description": "创建表单按钮",
                        "parameters": {"form_name": "默认表单"},
                        "expected_result": "打开表单设计器"
                    }
                ]
            }

    async def _validate_result(self, state: LowCodeDeveloperState) -> LowCodeDeveloperState:
        """验证实现结果"""
        try:
            logger.info("验证实现结果")

            # 截图当前状态
            screenshot_path = await self.operations.browser.take_screenshot()

            # 使用视觉识别分析结果
            analysis_result = await self.vision.analyze_screenshot(
                screenshot_path,
                "请分析这个页面，判断低代码功能是否实现成功"
            )

            # 基于分析结果判断是否成功
            success_indicators = [
                "保存成功",
                "创建完成",
                "配置成功",
                "表单已创建",
                "页面已生成"
            ]

            is_success = any(
                indicator in suggestion.lower()
                for suggestion in analysis_result.suggestions
                for indicator in success_indicators
            )

            if is_success or analysis_result.confidence_score > 0.7:
                state.solution.validation_result = ValidationResult(
                    is_valid=True,
                    score=analysis_result.confidence_score,
                    suggestions=analysis_result.suggestions
                )
                logger.info("验证成功")
            else:
                state.solution.validation_result = ValidationResult(
                    is_valid=False,
                    score=analysis_result.confidence_score,
                    issues=["实现结果不符合预期"],
                    suggestions=analysis_result.suggestions
                )
                logger.warning("验证失败")

            return state

        except Exception as e:
            logger.error(f"验证结果失败: {e}")
            state.error_count += 1
            return state

    async def _handle_error(self, state: LowCodeDeveloperState) -> LowCodeDeveloperState:
        """处理错误"""
        try:
            logger.info(f"处理错误，当前错误次数: {state.error_count}")

            if state.error_count >= state.max_errors:
                logger.error("错误次数过多，终止执行")
                state.solution.reward_decision = RewardDecision.REJECTED
                return state

            # 尝试回滚到最近的检查点
            if state.checkpoints and state.current_operation_index > 0:
                logger.info("尝试回滚到检查点")

                # 回滚到上一个检查点
                last_checkpoint = state.checkpoints[-1]

                # 重新加载页面状态（简化实现）
                await self.operations.browser.navigate_to_url(
                    state.session_info.platform_url if state.session_info else ""
                )

                # 减少操作索引，重新执行
                state.current_operation_index = max(0, state.current_operation_index - 1)

                logger.info(f"回滚完成，将重新执行操作 {state.current_operation_index}")

            return state

        except Exception as e:
            logger.error(f"处理错误失败: {e}")
            state.solution.reward_decision = RewardDecision.REJECTED
            return state

    async def _finalize_solution(self, state: LowCodeDeveloperState) -> LowCodeDeveloperState:
        """完成方案"""
        try:
            logger.info("完成实现方案")

            # 计算成功率
            successful_operations = sum(
                1 for op in state.solution.operations
                if op.success is True
            )
            total_operations = len(state.solution.operations)

            if total_operations > 0:
                state.solution.success_rate = successful_operations / total_operations
            else:
                state.solution.success_rate = 0.0

            # 设置奖励决策
            if state.solution.validation_result and state.solution.validation_result.is_valid:
                if state.solution.success_rate >= 0.8:
                    state.solution.reward_decision = RewardDecision.ACCEPTED
                else:
                    state.solution.reward_decision = RewardDecision.PENDING
            else:
                state.solution.reward_decision = RewardDecision.REJECTED

            # 计算总执行时间
            total_time = sum(
                op.execution_time or 0
                for op in state.solution.operations
            )
            state.solution.execution_time = total_time

            # 更新时间戳
            state.solution.updated_at = datetime.now()

            # 关闭操作工具
            await self.operations.close()

            logger.info(f"方案完成，成功率: {state.solution.success_rate:.2f}, 决策: {state.solution.reward_decision}")
            return state

        except Exception as e:
            logger.error(f"完成方案失败: {e}")
            state.solution.reward_decision = RewardDecision.REJECTED
            return state

    # 条件判断方法
    def _should_continue_after_auth(self, state: LowCodeDeveloperState) -> str:
        """判断认证后是否继续"""
        if state.is_authenticated:
            return "continue"
        elif state.error_count < state.max_errors:
            return "retry"
        else:
            return "error"

    def _should_continue_execution(self, state: LowCodeDeveloperState) -> str:
        """判断是否继续执行操作"""
        if state.error_count >= state.max_errors:
            return "error"
        elif state.current_operation_index >= len(state.solution.operations):
            return "validate"
        else:
            return "continue"

    def _should_continue_after_validation(self, state: LowCodeDeveloperState) -> str:
        """判断验证后是否继续"""
        if state.error_count >= state.max_errors:
            return "error"
        elif (state.solution.validation_result and
              state.solution.validation_result.is_valid):
            return "success"
        elif state.error_count < state.max_errors // 2:  # 允许重试
            return "retry"
        else:
            return "error"


# 创建全局智能体实例
low_code_developer_agent = LowCodeDeveloperAgent()
