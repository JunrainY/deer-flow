"""
低代码开发工作流

基于LangGraph的多智能体协作工作流
整合低代码开发、功能验证和知识管理智能体
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Literal
from enum import Enum

from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from ..models.low_code_models import (
    DevelopmentRequest,
    ImplementationSolution,
    RewardDecision,
    ValidationResult
)
from ..agents.low_code_developer import low_code_developer_agent
from ..agents.function_validator import function_validator_agent
from ..agents.knowledge_manager import knowledge_manager_agent


logger = logging.getLogger(__name__)


class WorkflowStage(str, Enum):
    """工作流阶段枚举"""
    INITIALIZATION = "initialization"
    KNOWLEDGE_SEARCH = "knowledge_search"
    DEVELOPMENT = "development"
    VALIDATION = "validation"
    REVIEW = "review"
    KNOWLEDGE_UPDATE = "knowledge_update"
    COMPLETION = "completion"


class LowCodeWorkflowState(BaseModel):
    """低代码开发工作流状态"""
    # 输入
    request: Optional[DevelopmentRequest] = None
    user_feedback: Optional[str] = None
    
    # 工作流状态
    current_stage: WorkflowStage = WorkflowStage.INITIALIZATION
    iteration_count: int = 0
    max_iterations: int = 3
    
    # 智能体输出
    similar_solutions: List[ImplementationSolution] = Field(default_factory=list)
    current_solution: Optional[ImplementationSolution] = None
    validation_result: Optional[ValidationResult] = None
    
    # 决策和反馈
    reward_decision: RewardDecision = RewardDecision.PENDING
    human_in_loop: bool = True
    auto_accept_threshold: float = 0.9
    
    # 错误处理
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # 结果
    final_solution: Optional[ImplementationSolution] = None
    workflow_completed: bool = False
    success: bool = False


class LowCodeWorkflow:
    """低代码开发工作流类"""
    
    def __init__(self):
        """初始化工作流"""
        self.graph = self._build_workflow_graph()
    
    def _build_workflow_graph(self) -> StateGraph:
        """构建工作流图"""
        graph = StateGraph(LowCodeWorkflowState)
        
        # 添加节点
        graph.add_node("initialize", self._initialize)
        graph.add_node("search_knowledge", self._search_knowledge)
        graph.add_node("develop_solution", self._develop_solution)
        graph.add_node("validate_solution", self._validate_solution)
        graph.add_node("review_solution", self._review_solution)
        graph.add_node("update_knowledge", self._update_knowledge)
        graph.add_node("finalize", self._finalize)
        graph.add_node("handle_error", self._handle_error)
        
        # 设置入口点
        graph.set_entry_point("initialize")
        
        # 添加边和条件边
        graph.add_edge("initialize", "search_knowledge")
        graph.add_edge("search_knowledge", "develop_solution")
        
        graph.add_conditional_edges(
            "develop_solution",
            self._after_development,
            {
                "validate": "validate_solution",
                "error": "handle_error",
                "retry": "develop_solution"
            }
        )
        
        graph.add_conditional_edges(
            "validate_solution",
            self._after_validation,
            {
                "review": "review_solution",
                "retry": "develop_solution",
                "error": "handle_error"
            }
        )
        
        graph.add_conditional_edges(
            "review_solution",
            self._after_review,
            {
                "accept": "update_knowledge",
                "reject": "develop_solution",
                "pending": "finalize"
            }
        )
        
        graph.add_edge("update_knowledge", "finalize")
        graph.add_edge("handle_error", "finalize")
        graph.add_edge("finalize", END)
        
        return graph.compile()
    
    async def execute(self, request: DevelopmentRequest, human_in_loop: bool = True) -> ImplementationSolution:
        """执行低代码开发工作流"""
        try:
            logger.info(f"开始执行低代码开发工作流: {request.title}")
            
            # 初始化状态
            initial_state = LowCodeWorkflowState(
                request=request,
                human_in_loop=human_in_loop,
                current_stage=WorkflowStage.INITIALIZATION
            )
            
            # 执行工作流
            final_state = await self.graph.ainvoke(initial_state)

            # 返回最终方案
            if hasattr(final_state, 'final_solution') and final_state.final_solution:
                logger.info(f"工作流执行完成: {final_state.final_solution.solution_id}")
                return final_state.final_solution
            elif hasattr(final_state, 'current_solution') and final_state.current_solution:
                logger.info(f"工作流执行完成: {final_state.current_solution.solution_id}")
                return final_state.current_solution
            else:
                logger.error("工作流执行失败，未生成有效方案")
                return ImplementationSolution(
                    request_id=request.request_id,
                    title=f"失败方案: {request.title}",
                    description="工作流执行失败",
                    operations=[],
                    reward_decision=RewardDecision.REJECTED
                )
                
        except Exception as e:
            logger.error(f"工作流执行异常: {e}")
            return ImplementationSolution(
                request_id=request.request_id,
                title=f"异常方案: {request.title}",
                description=f"工作流执行异常: {str(e)}",
                operations=[],
                reward_decision=RewardDecision.REJECTED
            )
    
    async def _initialize(self, state: LowCodeWorkflowState) -> LowCodeWorkflowState:
        """初始化工作流"""
        try:
            logger.info("初始化低代码开发工作流")
            
            state.current_stage = WorkflowStage.INITIALIZATION
            
            # 验证输入
            if not state.request:
                state.errors.append("缺少开发请求")
                return state
            
            # 记录开始时间
            state.request.created_at = datetime.now()
            
            logger.info(f"工作流初始化完成: {state.request.title}")
            return state
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            state.errors.append(f"初始化失败: {str(e)}")
            return state
    
    async def _search_knowledge(self, state: LowCodeWorkflowState) -> LowCodeWorkflowState:
        """搜索相关知识"""
        try:
            logger.info("搜索相关知识和历史方案")
            
            state.current_stage = WorkflowStage.KNOWLEDGE_SEARCH
            
            # 搜索相似方案
            similar_solutions = await knowledge_manager_agent.search_similar_solutions(state.request)
            state.similar_solutions = similar_solutions
            
            if similar_solutions:
                logger.info(f"找到{len(similar_solutions)}个相似方案")
                state.warnings.append(f"找到{len(similar_solutions)}个相似方案，可参考复用")
            else:
                logger.info("未找到相似方案，将从头开发")
            
            return state
            
        except Exception as e:
            logger.error(f"搜索知识失败: {e}")
            state.errors.append(f"搜索知识失败: {str(e)}")
            return state
    
    async def _develop_solution(self, state: LowCodeWorkflowState) -> LowCodeWorkflowState:
        """开发解决方案"""
        try:
            logger.info("开发低代码解决方案")
            
            state.current_stage = WorkflowStage.DEVELOPMENT
            state.iteration_count += 1
            
            # 使用低代码开发智能体开发方案
            solution = await low_code_developer_agent.develop(state.request)
            state.current_solution = solution
            
            # 检查开发结果
            if solution and solution.operations:
                logger.info(f"方案开发完成: {solution.solution_id}, 操作数: {len(solution.operations)}")
            else:
                logger.error("方案开发失败")
                state.errors.append("方案开发失败")
            
            return state
            
        except Exception as e:
            logger.error(f"开发方案失败: {e}")
            state.errors.append(f"开发方案失败: {str(e)}")
            return state
    
    async def _validate_solution(self, state: LowCodeWorkflowState) -> LowCodeWorkflowState:
        """验证解决方案"""
        try:
            logger.info("验证解决方案")
            
            state.current_stage = WorkflowStage.VALIDATION
            
            if not state.current_solution:
                state.errors.append("没有可验证的方案")
                return state
            
            # 使用功能验证智能体验证方案
            validation_result = await function_validator_agent.validate(state.current_solution)
            state.validation_result = validation_result
            
            # 更新方案的验证结果
            state.current_solution.update_validation_result(validation_result)
            
            if validation_result.is_valid:
                logger.info(f"方案验证通过: 得分 {validation_result.score:.2f}")
            else:
                logger.warning(f"方案验证失败: {len(validation_result.issues)} 个问题")
            
            return state
            
        except Exception as e:
            logger.error(f"验证方案失败: {e}")
            state.errors.append(f"验证方案失败: {str(e)}")
            return state
    
    async def _review_solution(self, state: LowCodeWorkflowState) -> LowCodeWorkflowState:
        """审查解决方案"""
        try:
            logger.info("审查解决方案")
            
            state.current_stage = WorkflowStage.REVIEW
            
            if not state.current_solution or not state.validation_result:
                state.errors.append("缺少方案或验证结果")
                return state
            
            # 自动决策逻辑
            if state.validation_result.is_valid and state.validation_result.score >= state.auto_accept_threshold:
                # 自动接受高质量方案
                state.reward_decision = RewardDecision.ACCEPTED
                logger.info(f"方案自动接受: 得分 {state.validation_result.score:.2f}")
                
            elif state.validation_result.is_valid and state.validation_result.score >= 0.7:
                # 中等质量方案，如果启用人在环中则等待人工审查
                if state.human_in_loop:
                    state.reward_decision = RewardDecision.PENDING
                    logger.info("方案等待人工审查")
                else:
                    state.reward_decision = RewardDecision.ACCEPTED
                    logger.info("方案自动接受（无人工审查）")
                    
            else:
                # 低质量方案，拒绝或重试
                if state.iteration_count < state.max_iterations:
                    state.reward_decision = RewardDecision.PENDING
                    logger.info("方案质量不足，准备重试")
                else:
                    state.reward_decision = RewardDecision.REJECTED
                    logger.info("方案质量不足且达到最大重试次数，拒绝方案")
            
            return state
            
        except Exception as e:
            logger.error(f"审查方案失败: {e}")
            state.errors.append(f"审查方案失败: {str(e)}")
            return state
    
    async def _update_knowledge(self, state: LowCodeWorkflowState) -> LowCodeWorkflowState:
        """更新知识库"""
        try:
            logger.info("更新知识库")
            
            state.current_stage = WorkflowStage.KNOWLEDGE_UPDATE
            
            if not state.current_solution:
                state.errors.append("没有可存储的方案")
                return state
            
            # 存储方案到知识库
            success = await knowledge_manager_agent.store_solution(
                state.current_solution,
                state.reward_decision
            )
            
            if success:
                logger.info("知识库更新成功")
            else:
                logger.error("知识库更新失败")
                state.warnings.append("知识库更新失败")
            
            return state
            
        except Exception as e:
            logger.error(f"更新知识库失败: {e}")
            state.errors.append(f"更新知识库失败: {str(e)}")
            return state
    
    async def _finalize(self, state: LowCodeWorkflowState) -> LowCodeWorkflowState:
        """完成工作流"""
        try:
            logger.info("完成工作流")
            
            state.current_stage = WorkflowStage.COMPLETION
            state.workflow_completed = True
            
            # 设置最终方案
            if state.current_solution and state.reward_decision != RewardDecision.REJECTED:
                state.final_solution = state.current_solution
                state.success = True
                logger.info(f"工作流成功完成: {state.final_solution.solution_id}")
            else:
                logger.warning("工作流完成但未产生有效方案")
                state.success = False
            
            return state
            
        except Exception as e:
            logger.error(f"完成工作流失败: {e}")
            state.errors.append(f"完成工作流失败: {str(e)}")
            return state
    
    async def _handle_error(self, state: LowCodeWorkflowState) -> LowCodeWorkflowState:
        """处理错误"""
        try:
            logger.error(f"处理工作流错误: {len(state.errors)} 个错误")
            
            # 记录错误信息
            for error in state.errors:
                logger.error(f"工作流错误: {error}")
            
            # 设置失败状态
            state.workflow_completed = True
            state.success = False
            
            return state
            
        except Exception as e:
            logger.error(f"错误处理失败: {e}")
            return state
    
    # 条件判断方法
    def _after_development(self, state: LowCodeWorkflowState) -> Literal["validate", "error", "retry"]:
        """开发后的条件判断"""
        if state.errors:
            return "error"
        elif not state.current_solution or not state.current_solution.operations:
            if state.iteration_count < state.max_iterations:
                return "retry"
            else:
                return "error"
        else:
            return "validate"
    
    def _after_validation(self, state: LowCodeWorkflowState) -> Literal["review", "retry", "error"]:
        """验证后的条件判断"""
        if state.errors:
            return "error"
        elif not state.validation_result:
            return "error"
        else:
            return "review"
    
    def _after_review(self, state: LowCodeWorkflowState) -> Literal["accept", "reject", "pending"]:
        """审查后的条件判断"""
        if state.reward_decision == RewardDecision.ACCEPTED:
            return "accept"
        elif state.reward_decision == RewardDecision.REJECTED:
            return "reject"
        else:
            return "pending"


# 创建全局工作流实例
low_code_workflow = LowCodeWorkflow()
