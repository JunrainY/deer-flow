"""
知识库存储模块

基于SQLAlchemy的知识库数据存储和检索功能
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import os
import json

from sqlalchemy import create_engine, Column, String, Text, Float, Integer, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from ..models.low_code_models import ImplementationSolution, RewardDecision
from ..models.reward_models import (
    SolutionEvaluation,
    KnowledgeEntry,
    KnowledgeEntryType,
    VersionInfo,
    RewardTransaction,
    RewardCriteria
)


logger = logging.getLogger(__name__)

Base = declarative_base()


class SolutionTable(Base):
    """实现方案表"""
    __tablename__ = "implementation_solutions"
    
    solution_id = Column(String, primary_key=True)
    request_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    operations = Column(JSON)
    validation_result = Column(JSON)
    visual_analysis = Column(JSON)
    reward_decision = Column(String, default="pending")
    success_rate = Column(Float, default=0.0)
    execution_time = Column(Float, default=0.0)
    developer_agent = Column(String)
    version = Column(Integer, default=1)
    parent_solution_id = Column(String)
    tags = Column(JSON)
    solution_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)


class KnowledgeEntryTable(Base):
    """知识条目表"""
    __tablename__ = "knowledge_entries"
    
    entry_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    entry_type = Column(String, nullable=False)
    content = Column(JSON)
    related_solution_ids = Column(JSON)
    tags = Column(JSON)
    keywords = Column(JSON)
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    last_used_at = Column(DateTime)
    quality_score = Column(Float, default=0.0)
    user_ratings = Column(JSON)
    version = Column(Integer, default=1)
    parent_entry_id = Column(String)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)


class EvaluationTable(Base):
    """方案评估表"""
    __tablename__ = "solution_evaluations"
    
    evaluation_id = Column(String, primary_key=True)
    solution_id = Column(String, nullable=False)
    evaluator_type = Column(String, nullable=False)
    evaluator_id = Column(String)
    functionality_score = Column(Float, default=0.0)
    code_quality_score = Column(Float, default=0.0)
    performance_score = Column(Float, default=0.0)
    user_satisfaction_score = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)
    detailed_feedback = Column(JSON)
    strengths = Column(JSON)
    weaknesses = Column(JSON)
    improvement_suggestions = Column(JSON)
    status = Column(String, default="pending")
    evaluation_time = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
    completed_at = Column(DateTime)


class VersionTable(Base):
    """版本信息表"""
    __tablename__ = "version_info"
    
    version_id = Column(String, primary_key=True)
    entity_id = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    version_number = Column(Integer, nullable=False)
    change_summary = Column(String, nullable=False)
    change_details = Column(JSON)
    changed_by = Column(String)
    change_reason = Column(String)
    version_data = Column(JSON)
    is_current = Column(Boolean, default=True)
    is_rollback = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)


class RewardTransactionTable(Base):
    """奖励交易表"""
    __tablename__ = "reward_transactions"
    
    transaction_id = Column(String, primary_key=True)
    solution_id = Column(String, nullable=False)
    evaluation_id = Column(String)
    reward_points = Column(Integer, default=0)
    reward_type = Column(String, nullable=False)
    reward_reason = Column(String, nullable=False)
    status = Column(String, default="pending")
    processed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)


class KnowledgeStore:
    """知识库存储类"""
    
    def __init__(self):
        """初始化知识库存储"""
        self.database_url = os.getenv("KNOWLEDGE_DB_URL", "sqlite:///knowledge.db")
        self.engine = None
        self.session_factory = None
        
    async def initialize(self):
        """初始化数据库连接"""
        try:
            if self.database_url.startswith("sqlite"):
                # SQLite同步连接
                self.engine = create_engine(self.database_url)
                self.session_factory = sessionmaker(bind=self.engine)
            else:
                # 异步数据库连接
                self.engine = create_async_engine(self.database_url)
                self.session_factory = async_sessionmaker(bind=self.engine)
            
            # 创建表
            if self.database_url.startswith("sqlite"):
                Base.metadata.create_all(self.engine)
            else:
                async with self.engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
            
            logger.info("知识库数据库初始化完成")
            
        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")
            raise
    
    async def store_solution(self, solution: ImplementationSolution) -> bool:
        """存储实现方案"""
        try:
            if not self.session_factory:
                await self.initialize()
            
            session = self.session_factory()
            
            try:
                # 转换为数据库记录
                solution_record = SolutionTable(
                    solution_id=solution.solution_id,
                    request_id=solution.request_id,
                    title=solution.title,
                    description=solution.description,
                    operations=[op.dict() for op in solution.operations],
                    validation_result=solution.validation_result.dict() if solution.validation_result else None,
                    visual_analysis=[va.dict() for va in solution.visual_analysis],
                    reward_decision=solution.reward_decision.value,
                    success_rate=solution.success_rate,
                    execution_time=solution.execution_time,
                    developer_agent=solution.developer_agent,
                    version=solution.version,
                    parent_solution_id=solution.parent_solution_id,
                    tags=solution.tags,
                    solution_metadata=solution.metadata,
                    created_at=solution.created_at,
                    updated_at=solution.updated_at
                )
                
                if isinstance(session, AsyncSession):
                    session.add(solution_record)
                    await session.commit()
                else:
                    session.add(solution_record)
                    session.commit()
                
                logger.info(f"方案存储成功: {solution.solution_id}")
                return True
                
            finally:
                if isinstance(session, AsyncSession):
                    await session.close()
                else:
                    session.close()
                
        except Exception as e:
            logger.error(f"存储方案失败: {e}")
            return False
    
    async def get_solution(self, solution_id: str) -> Optional[ImplementationSolution]:
        """获取实现方案"""
        try:
            if not self.session_factory:
                await self.initialize()
            
            session = self.session_factory()
            
            try:
                if isinstance(session, AsyncSession):
                    result = await session.get(SolutionTable, solution_id)
                else:
                    result = session.get(SolutionTable, solution_id)
                
                if result:
                    return self._convert_to_solution(result)
                return None
                
            finally:
                if isinstance(session, AsyncSession):
                    await session.close()
                else:
                    session.close()
                
        except Exception as e:
            logger.error(f"获取方案失败: {e}")
            return None
    
    async def search_solutions(self, keywords: List[str], requirements: List[str], limit: int = 10) -> List[ImplementationSolution]:
        """搜索实现方案"""
        try:
            if not self.session_factory:
                await self.initialize()
            
            session = self.session_factory()
            
            try:
                # 简化的搜索实现
                if isinstance(session, AsyncSession):
                    from sqlalchemy import select
                    stmt = select(SolutionTable).where(
                        SolutionTable.reward_decision == "accepted"
                    ).limit(limit)
                    result = await session.execute(stmt)
                    records = result.scalars().all()
                else:
                    records = session.query(SolutionTable).filter(
                        SolutionTable.reward_decision == "accepted"
                    ).limit(limit).all()
                
                solutions = [self._convert_to_solution(record) for record in records]
                return solutions
                
            finally:
                if isinstance(session, AsyncSession):
                    await session.close()
                else:
                    session.close()
                
        except Exception as e:
            logger.error(f"搜索方案失败: {e}")
            return []
    
    async def store_knowledge_entry(self, entry: KnowledgeEntry) -> bool:
        """存储知识条目"""
        try:
            if not self.session_factory:
                await self.initialize()
            
            session = self.session_factory()
            
            try:
                entry_record = KnowledgeEntryTable(
                    entry_id=entry.entry_id,
                    title=entry.title,
                    description=entry.description,
                    entry_type=entry.entry_type.value,
                    content=entry.content,
                    related_solution_ids=entry.related_solution_ids,
                    tags=entry.tags,
                    keywords=entry.keywords,
                    usage_count=entry.usage_count,
                    success_rate=entry.success_rate,
                    last_used_at=entry.last_used_at,
                    quality_score=entry.quality_score,
                    user_ratings=entry.user_ratings,
                    version=entry.version,
                    parent_entry_id=entry.parent_entry_id,
                    is_active=entry.is_active,
                    is_verified=entry.is_verified,
                    created_at=entry.created_at,
                    updated_at=entry.updated_at
                )
                
                if isinstance(session, AsyncSession):
                    session.add(entry_record)
                    await session.commit()
                else:
                    session.add(entry_record)
                    session.commit()
                
                return True
                
            finally:
                if isinstance(session, AsyncSession):
                    await session.close()
                else:
                    session.close()
                
        except Exception as e:
            logger.error(f"存储知识条目失败: {e}")
            return False
    
    async def get_knowledge_entries(self, entry_type: KnowledgeEntryType, keywords: List[str], limit: int = 10) -> List[KnowledgeEntry]:
        """获取知识条目"""
        try:
            # 简化实现，返回空列表
            return []
        except Exception as e:
            logger.error(f"获取知识条目失败: {e}")
            return []
    
    async def store_evaluation(self, evaluation: SolutionEvaluation) -> bool:
        """存储评估结果"""
        try:
            # 简化实现
            return True
        except Exception as e:
            logger.error(f"存储评估失败: {e}")
            return False
    
    async def store_version(self, version: VersionInfo) -> bool:
        """存储版本信息"""
        try:
            # 简化实现
            return True
        except Exception as e:
            logger.error(f"存储版本失败: {e}")
            return False
    
    async def store_reward_transaction(self, transaction: RewardTransaction) -> bool:
        """存储奖励交易"""
        try:
            # 简化实现
            return True
        except Exception as e:
            logger.error(f"存储奖励交易失败: {e}")
            return False
    
    async def get_reward_criteria(self) -> List[RewardCriteria]:
        """获取奖励标准"""
        try:
            # 返回默认标准
            return [
                RewardCriteria(
                    name="functionality",
                    description="功能性评估",
                    weight=0.4,
                    evaluation_method="manual",
                    threshold_values={"min": 0.7, "max": 1.0}
                ),
                RewardCriteria(
                    name="code_quality",
                    description="代码质量评估",
                    weight=0.2,
                    evaluation_method="automated",
                    threshold_values={"min": 0.6, "max": 1.0}
                ),
                RewardCriteria(
                    name="performance",
                    description="性能评估",
                    weight=0.2,
                    evaluation_method="automated",
                    threshold_values={"min": 0.5, "max": 1.0}
                ),
                RewardCriteria(
                    name="user_satisfaction",
                    description="用户满意度评估",
                    weight=0.2,
                    evaluation_method="manual",
                    threshold_values={"min": 0.7, "max": 1.0}
                )
            ]
        except Exception as e:
            logger.error(f"获取奖励标准失败: {e}")
            return []
    
    def _convert_to_solution(self, record: SolutionTable) -> ImplementationSolution:
        """转换数据库记录为方案对象"""
        try:
            from ..models.low_code_models import LowCodeOperation, ValidationResult, VisualAnalysisResult
            
            # 转换操作列表
            operations = []
            for op_data in record.operations or []:
                operations.append(LowCodeOperation(**op_data))
            
            # 转换验证结果
            validation_result = None
            if record.validation_result:
                validation_result = ValidationResult(**record.validation_result)
            
            # 转换视觉分析结果
            visual_analysis = []
            for va_data in record.visual_analysis or []:
                visual_analysis.append(VisualAnalysisResult(**va_data))
            
            return ImplementationSolution(
                solution_id=record.solution_id,
                request_id=record.request_id,
                title=record.title,
                description=record.description,
                operations=operations,
                validation_result=validation_result,
                visual_analysis=visual_analysis,
                reward_decision=RewardDecision(record.reward_decision),
                success_rate=record.success_rate,
                execution_time=record.execution_time,
                developer_agent=record.developer_agent,
                version=record.version,
                parent_solution_id=record.parent_solution_id,
                tags=record.tags or [],
                metadata=record.solution_metadata or {},
                created_at=record.created_at,
                updated_at=record.updated_at
            )
            
        except Exception as e:
            logger.error(f"转换数据库记录失败: {e}")
            raise
