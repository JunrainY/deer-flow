"""
低代码平台智能体系统核心数据模型

定义了开发请求、操作、验证结果等核心业务模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid


def generate_uuid() -> str:
    """生成UUID字符串"""
    return str(uuid.uuid4())


class OperationType(str, Enum):
    """操作类型枚举"""
    DATA_MODELING = "data_modeling"
    FORM_DESIGN = "form_design"
    PAGE_DESIGN = "page_design"
    WORKFLOW_DESIGN = "workflow_design"
    REPORT_DESIGN = "report_design"
    DICTIONARY_MANAGEMENT = "dictionary_management"
    NAVIGATION = "navigation"
    AUTHENTICATION = "authentication"


class ActionType(str, Enum):
    """动作类型枚举"""
    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    DRAG_DROP = "drag_drop"
    HOVER = "hover"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    VALIDATE = "validate"


class RewardDecision(str, Enum):
    """奖励决策枚举"""
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PENDING = "pending"


class Priority(int, Enum):
    """优先级枚举"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


class DevelopmentRequest(BaseModel):
    """开发需求模型"""
    request_id: str = Field(default_factory=generate_uuid, description="请求唯一标识")
    title: str = Field(..., description="需求标题")
    description: str = Field(..., description="功能描述")
    requirements: List[str] = Field(..., description="具体需求列表")
    priority: Priority = Field(default=Priority.MEDIUM, description="优先级")
    requester: Optional[str] = Field(None, description="需求提出者")
    deadline: Optional[datetime] = Field(None, description="截止时间")
    tags: List[str] = Field(default_factory=list, description="标签")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LowCodeOperation(BaseModel):
    """低代码平台操作模型"""
    operation_id: str = Field(default_factory=generate_uuid, description="操作唯一标识")
    operation_type: OperationType = Field(..., description="操作类型")
    action: ActionType = Field(..., description="具体操作动作")
    target_element: str = Field(..., description="目标元素选择器")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="操作参数")
    expected_result: Optional[str] = Field(None, description="预期结果")
    timeout: int = Field(default=30, description="超时时间(秒)")
    retry_count: int = Field(default=0, description="重试次数")
    max_retries: int = Field(default=3, description="最大重试次数")
    screenshot_before: Optional[str] = Field(None, description="操作前截图路径")
    screenshot_after: Optional[str] = Field(None, description="操作后截图路径")
    execution_time: Optional[float] = Field(None, description="执行时间(秒)")
    success: Optional[bool] = Field(None, description="执行是否成功")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ValidationResult(BaseModel):
    """验证结果模型"""
    validation_id: str = Field(default_factory=generate_uuid, description="验证唯一标识")
    is_valid: bool = Field(..., description="验证是否通过")
    score: float = Field(default=0.0, ge=0.0, le=1.0, description="验证得分")
    issues: List[str] = Field(default_factory=list, description="发现的问题")
    suggestions: List[str] = Field(default_factory=list, description="改进建议")
    test_results: Dict[str, Any] = Field(default_factory=dict, description="详细测试结果")
    performance_metrics: Dict[str, float] = Field(default_factory=dict, description="性能指标")
    validation_time: float = Field(default=0.0, description="验证耗时(秒)")
    validator_agent: Optional[str] = Field(None, description="验证智能体标识")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VisualAnalysisResult(BaseModel):
    """视觉分析结果模型"""
    analysis_id: str = Field(default_factory=generate_uuid, description="分析唯一标识")
    screenshot_path: str = Field(..., description="截图文件路径")
    elements: List[Dict[str, Any]] = Field(..., description="识别的UI元素")
    layout_info: Dict[str, Any] = Field(..., description="页面布局信息")
    suggestions: List[str] = Field(default_factory=list, description="操作建议")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="置信度")
    analysis_time: float = Field(default=0.0, description="分析耗时(秒)")
    model_used: Optional[str] = Field(None, description="使用的视觉模型")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ImplementationSolution(BaseModel):
    """实现方案模型"""
    solution_id: str = Field(default_factory=generate_uuid, description="方案唯一标识")
    request_id: str = Field(..., description="关联的开发请求ID")
    title: str = Field(..., description="方案标题")
    description: Optional[str] = Field(None, description="方案描述")
    operations: List[LowCodeOperation] = Field(..., description="操作序列")
    validation_result: Optional[ValidationResult] = Field(None, description="验证结果")
    visual_analysis: List[VisualAnalysisResult] = Field(default_factory=list, description="视觉分析结果")
    reward_decision: RewardDecision = Field(default=RewardDecision.PENDING, description="奖励决策")
    success_rate: float = Field(0.0, ge=0.0, le=1.0, description="成功率")
    execution_time: float = Field(default=0.0, description="总执行时间(秒)")
    developer_agent: Optional[str] = Field(None, description="开发智能体标识")
    version: int = Field(default=1, description="方案版本号")
    parent_solution_id: Optional[str] = Field(None, description="父方案ID(用于版本控制)")
    tags: List[str] = Field(default_factory=list, description="标签")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def add_operation(self, operation: LowCodeOperation) -> None:
        """添加操作到方案中"""
        self.operations.append(operation)
        self.updated_at = datetime.now()

    def update_validation_result(self, result: ValidationResult) -> None:
        """更新验证结果"""
        self.validation_result = result
        self.updated_at = datetime.now()

    def add_visual_analysis(self, analysis: VisualAnalysisResult) -> None:
        """添加视觉分析结果"""
        self.visual_analysis.append(analysis)
        self.updated_at = datetime.now()


class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: str = Field(default_factory=generate_uuid, description="会话唯一标识")
    user_id: Optional[str] = Field(None, description="用户ID")
    platform_url: str = Field(..., description="低代码平台URL")
    browser_context: Optional[str] = Field(None, description="浏览器上下文标识")
    is_authenticated: bool = Field(default=False, description="是否已认证")
    last_activity: datetime = Field(default_factory=datetime.now, description="最后活动时间")
    active_requests: List[str] = Field(default_factory=list, description="活跃的请求ID列表")
    session_data: Dict[str, Any] = Field(default_factory=dict, description="会话数据")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class OperationCheckpoint(BaseModel):
    """操作检查点模型"""
    checkpoint_id: str = Field(default_factory=generate_uuid, description="检查点唯一标识")
    solution_id: str = Field(..., description="关联的方案ID")
    operation_index: int = Field(..., description="操作索引")
    state_snapshot: Dict[str, Any] = Field(..., description="状态快照")
    screenshot_path: Optional[str] = Field(None, description="检查点截图")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
