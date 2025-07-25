"""
低代码智能体系统测试

测试低代码开发、功能验证和知识管理智能体的基本功能
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.models.low_code_models import (
    DevelopmentRequest,
    ImplementationSolution,
    LowCodeOperation,
    OperationType,
    ActionType,
    RewardDecision,
    ValidationResult
)
from src.agents.low_code_developer import LowCodeDeveloperAgent
from src.agents.function_validator import FunctionValidatorAgent
from src.agents.knowledge_manager import KnowledgeManagerAgent
from src.graph.low_code_workflow import LowCodeWorkflow


class TestLowCodeDeveloperAgent:
    """测试低代码开发智能体"""
    
    @pytest.fixture
    def sample_request(self):
        """示例开发请求"""
        return DevelopmentRequest(
            request_id="test-001",
            title="用户管理表单",
            description="创建一个用户信息管理表单，包含基本字段和操作功能",
            requirements=[
                "用户名输入框",
                "邮箱输入框",
                "电话号码输入框",
                "提交按钮",
                "重置按钮"
            ],
            priority=2
        )
    
    @pytest.mark.asyncio
    async def test_developer_agent_initialization(self):
        """测试开发智能体初始化"""
        agent = LowCodeDeveloperAgent()
        assert agent is not None
        assert agent.llm is not None
        assert agent.operations is not None
        assert agent.vision is not None
        assert agent.graph is not None
    
    @pytest.mark.asyncio
    async def test_develop_basic_functionality(self, sample_request):
        """测试基本开发功能"""
        agent = LowCodeDeveloperAgent()
        
        # Mock外部依赖
        with patch.object(agent.operations, 'initialize', return_value=True), \
             patch.object(agent.operations, 'authenticate', return_value=True), \
             patch.object(agent.operations.browser, 'execute_operation', return_value=True), \
             patch.object(agent.operations.browser, 'take_screenshot', return_value="test.png"), \
             patch.object(agent.vision, 'find_element_suggestions', return_value=["[data-testid='submit']"]):
            
            result = await agent.develop(sample_request)
            
            assert result is not None
            assert result.request_id == sample_request.request_id
            assert isinstance(result, ImplementationSolution)


class TestFunctionValidatorAgent:
    """测试功能验证智能体"""
    
    @pytest.fixture
    def sample_solution(self):
        """示例实现方案"""
        operations = [
            LowCodeOperation(
                operation_type=OperationType.FORM_DESIGN,
                action=ActionType.CLICK,
                target_element="[data-testid='create-form']",
                parameters={"form_name": "用户表单"}
            ),
            LowCodeOperation(
                operation_type=OperationType.FORM_DESIGN,
                action=ActionType.FILL,
                target_element="[data-testid='field-name']",
                parameters={"value": "用户名"}
            )
        ]
        
        return ImplementationSolution(
            request_id="test-001",
            title="用户管理表单实现",
            description="用户管理表单的具体实现",
            operations=operations
        )
    
    @pytest.mark.asyncio
    async def test_validator_agent_initialization(self):
        """测试验证智能体初始化"""
        agent = FunctionValidatorAgent()
        assert agent is not None
        assert agent.llm is not None
        assert agent.browser is not None
        assert agent.vision is not None
        assert agent.graph is not None
    
    @pytest.mark.asyncio
    async def test_validate_solution(self, sample_solution):
        """测试方案验证功能"""
        agent = FunctionValidatorAgent()
        
        # Mock外部依赖
        with patch.object(agent.browser, 'start_browser', return_value=True), \
             patch.object(agent.browser, 'navigate_to_url', return_value=True), \
             patch.object(agent.browser, 'take_screenshot', return_value="test.png"), \
             patch.object(agent.vision, 'analyze_screenshot') as mock_analyze:
            
            # 设置mock返回值
            mock_analyze.return_value = AsyncMock()
            mock_analyze.return_value.confidence_score = 0.8
            mock_analyze.return_value.suggestions = ["功能实现正确"]
            
            result = await agent.validate(sample_solution)
            
            assert result is not None
            assert isinstance(result, ValidationResult)
            assert result.validator_agent == "function_validator"


class TestKnowledgeManagerAgent:
    """测试知识管理智能体"""
    
    @pytest.fixture
    def sample_solution(self):
        """示例实现方案"""
        return ImplementationSolution(
            request_id="test-001",
            title="用户管理表单实现",
            description="用户管理表单的具体实现",
            operations=[],
            reward_decision=RewardDecision.ACCEPTED,
            success_rate=0.9
        )
    
    @pytest.mark.asyncio
    async def test_knowledge_manager_initialization(self):
        """测试知识管理智能体初始化"""
        agent = KnowledgeManagerAgent()
        assert agent is not None
        assert agent.llm is not None
        assert agent.knowledge_store is not None
    
    @pytest.mark.asyncio
    async def test_store_solution(self, sample_solution):
        """测试方案存储功能"""
        agent = KnowledgeManagerAgent()
        
        # Mock数据库操作
        with patch.object(agent.knowledge_store, 'store_solution', return_value=True), \
             patch.object(agent.knowledge_store, 'store_knowledge_entry', return_value=True), \
             patch.object(agent.knowledge_store, 'store_reward_transaction', return_value=True):
            
            result = await agent.store_solution(sample_solution, RewardDecision.ACCEPTED)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_search_similar_solutions(self):
        """测试相似方案搜索"""
        agent = KnowledgeManagerAgent()
        
        request = DevelopmentRequest(
            request_id="test-002",
            title="员工管理表单",
            description="创建员工信息管理表单",
            requirements=["姓名", "部门", "职位"]
        )
        
        # Mock搜索结果
        with patch.object(agent.knowledge_store, 'search_solutions', return_value=[]):
            
            result = await agent.search_similar_solutions(request)
            
            assert isinstance(result, list)


class TestLowCodeWorkflow:
    """测试低代码开发工作流"""
    
    @pytest.fixture
    def sample_request(self):
        """示例开发请求"""
        return DevelopmentRequest(
            request_id="test-workflow-001",
            title="产品管理系统",
            description="创建产品信息管理系统",
            requirements=[
                "产品列表页面",
                "产品详情页面",
                "产品编辑表单",
                "产品搜索功能"
            ]
        )
    
    @pytest.mark.asyncio
    async def test_workflow_initialization(self):
        """测试工作流初始化"""
        workflow = LowCodeWorkflow()
        assert workflow is not None
        assert workflow.graph is not None
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self, sample_request):
        """测试工作流执行"""
        workflow = LowCodeWorkflow()
        
        # Mock所有智能体的操作
        with patch('src.agents.low_code_developer.low_code_developer_agent') as mock_dev, \
             patch('src.agents.function_validator.function_validator_agent') as mock_val, \
             patch('src.agents.knowledge_manager.knowledge_manager_agent') as mock_km:
            
            # 设置mock返回值
            mock_solution = ImplementationSolution(
                request_id=sample_request.request_id,
                title="测试方案",
                description="测试方案描述",
                operations=[],
                success_rate=0.8
            )
            
            mock_validation = ValidationResult(
                is_valid=True,
                score=0.8,
                validator_agent="test"
            )
            
            mock_dev.develop.return_value = mock_solution
            mock_val.validate.return_value = mock_validation
            mock_km.search_similar_solutions.return_value = []
            mock_km.store_solution.return_value = True
            
            result = await workflow.execute(sample_request, human_in_loop=False)
            
            assert result is not None
            assert isinstance(result, ImplementationSolution)


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """端到端工作流测试"""
        # 创建开发请求
        request = DevelopmentRequest(
            request_id="integration-test-001",
            title="客户管理系统",
            description="创建客户信息管理系统",
            requirements=[
                "客户列表",
                "客户详情",
                "新增客户",
                "编辑客户",
                "删除客户"
            ]
        )
        
        # 执行工作流
        workflow = LowCodeWorkflow()
        
        # 由于需要真实的浏览器环境，这里只测试工作流的基本结构
        assert workflow.graph is not None
        
        # 在实际环境中，可以执行完整的工作流
        # result = await workflow.execute(request, human_in_loop=False)
        # assert result is not None


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
