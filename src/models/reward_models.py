"""
奖励机制相关数据模型

定义了评估标准、方案评价、知识条目等奖励系统相关模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


def generate_uuid() -> str:
    """生成UUID字符串"""
    return str(uuid.uuid4())


class EvaluationStatus(str, Enum):
    """评估状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class KnowledgeEntryType(str, Enum):
    """知识条目类型枚举"""
    SOLUTION_PATTERN = "solution_pattern"
    BEST_PRACTICE = "best_practice"
    COMMON_ISSUE = "common_issue"
    OPTIMIZATION_TIP = "optimization_tip"


class RewardCriteria(BaseModel):
    """奖励评估标准模型"""
    criteria_id: str = Field(default_factory=generate_uuid, description="标准唯一标识")
    name: str = Field(..., description="标准名称")
    description: str = Field(..., description="标准描述")
    weight: float = Field(..., ge=0.0, le=1.0, description="权重")
    evaluation_method: str = Field(..., description="评估方法")
    threshold_values: Dict[str, float] = Field(..., description="阈值配置")
    is_active: bool = Field(default=True, description="是否启用")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SolutionEvaluation(BaseModel):
    """方案评估模型"""
    evaluation_id: str = Field(default_factory=generate_uuid, description="评估唯一标识")
    solution_id: str = Field(..., description="关联的方案ID")
    evaluator_type: str = Field(..., description="评估者类型(human/ai)")
    evaluator_id: Optional[str] = Field(None, description="评估者标识")
    
    # 评估分数
    functionality_score: float = Field(0.0, ge=0.0, le=1.0, description="功能性得分")
    code_quality_score: float = Field(0.0, ge=0.0, le=1.0, description="代码质量得分")
    performance_score: float = Field(0.0, ge=0.0, le=1.0, description="性能得分")
    user_satisfaction_score: float = Field(0.0, ge=0.0, le=1.0, description="用户满意度得分")
    overall_score: float = Field(0.0, ge=0.0, le=1.0, description="综合得分")
    
    # 详细评估
    detailed_feedback: Dict[str, Any] = Field(default_factory=dict, description="详细反馈")
    strengths: List[str] = Field(default_factory=list, description="优点")
    weaknesses: List[str] = Field(default_factory=list, description="缺点")
    improvement_suggestions: List[str] = Field(default_factory=list, description="改进建议")
    
    # 评估状态
    status: EvaluationStatus = Field(default=EvaluationStatus.PENDING, description="评估状态")
    evaluation_time: float = Field(default=0.0, description="评估耗时(秒)")
    
    # 时间信息
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def calculate_overall_score(self, criteria: List[RewardCriteria]) -> float:
        """根据评估标准计算综合得分"""
        if not criteria:
            return 0.0
            
        weighted_sum = 0.0
        total_weight = 0.0
        
        for criterion in criteria:
            if criterion.name == "functionality":
                weighted_sum += self.functionality_score * criterion.weight
            elif criterion.name == "code_quality":
                weighted_sum += self.code_quality_score * criterion.weight
            elif criterion.name == "performance":
                weighted_sum += self.performance_score * criterion.weight
            elif criterion.name == "user_satisfaction":
                weighted_sum += self.user_satisfaction_score * criterion.weight
            
            total_weight += criterion.weight
        
        self.overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        return self.overall_score


class KnowledgeEntry(BaseModel):
    """知识库条目模型"""
    entry_id: str = Field(default_factory=generate_uuid, description="条目唯一标识")
    title: str = Field(..., description="条目标题")
    description: str = Field(..., description="条目描述")
    entry_type: KnowledgeEntryType = Field(..., description="条目类型")
    content: Dict[str, Any] = Field(..., description="条目内容")
    
    # 关联信息
    related_solution_ids: List[str] = Field(default_factory=list, description="关联的方案ID列表")
    tags: List[str] = Field(default_factory=list, description="标签")
    keywords: List[str] = Field(default_factory=list, description="关键词")
    
    # 使用统计
    usage_count: int = Field(default=0, description="使用次数")
    success_rate: float = Field(0.0, ge=0.0, le=1.0, description="成功率")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    
    # 质量评估
    quality_score: float = Field(0.0, ge=0.0, le=1.0, description="质量得分")
    user_ratings: List[float] = Field(default_factory=list, description="用户评分列表")
    
    # 版本信息
    version: int = Field(default=1, description="版本号")
    parent_entry_id: Optional[str] = Field(None, description="父条目ID")
    
    # 状态信息
    is_active: bool = Field(default=True, description="是否启用")
    is_verified: bool = Field(default=False, description="是否已验证")
    
    # 时间信息
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def add_usage(self, success: bool = True) -> None:
        """记录使用情况"""
        self.usage_count += 1
        self.last_used_at = datetime.now()
        
        # 更新成功率
        if self.usage_count == 1:
            self.success_rate = 1.0 if success else 0.0
        else:
            current_successes = self.success_rate * (self.usage_count - 1)
            if success:
                current_successes += 1
            self.success_rate = current_successes / self.usage_count

    def add_rating(self, rating: float) -> None:
        """添加用户评分"""
        if 0.0 <= rating <= 1.0:
            self.user_ratings.append(rating)
            # 重新计算质量得分
            self.quality_score = sum(self.user_ratings) / len(self.user_ratings)


class VersionInfo(BaseModel):
    """版本信息模型"""
    version_id: str = Field(default_factory=generate_uuid, description="版本唯一标识")
    entity_id: str = Field(..., description="实体ID(方案ID或条目ID)")
    entity_type: str = Field(..., description="实体类型")
    version_number: int = Field(..., description="版本号")
    
    # 变更信息
    change_summary: str = Field(..., description="变更摘要")
    change_details: Dict[str, Any] = Field(default_factory=dict, description="变更详情")
    changed_by: Optional[str] = Field(None, description="变更者")
    change_reason: Optional[str] = Field(None, description="变更原因")
    
    # 版本数据
    version_data: Dict[str, Any] = Field(..., description="版本数据快照")
    
    # 状态信息
    is_current: bool = Field(default=True, description="是否为当前版本")
    is_rollback: bool = Field(default=False, description="是否为回滚版本")
    
    # 时间信息
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RewardTransaction(BaseModel):
    """奖励交易记录模型"""
    transaction_id: str = Field(default_factory=generate_uuid, description="交易唯一标识")
    solution_id: str = Field(..., description="关联的方案ID")
    evaluation_id: str = Field(..., description="关联的评估ID")
    
    # 奖励信息
    reward_points: int = Field(default=0, description="奖励积分")
    reward_type: str = Field(..., description="奖励类型")
    reward_reason: str = Field(..., description="奖励原因")
    
    # 交易状态
    status: str = Field(default="pending", description="交易状态")
    processed_at: Optional[datetime] = Field(None, description="处理时间")
    
    # 时间信息
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
