"""
知识管理智能体

管理实现方案的存储、检索和奖励机制
负责建立可复用的实现方案库
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import json
import hashlib

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ..models.low_code_models import (
    ImplementationSolution,
    RewardDecision,
    DevelopmentRequest
)
from ..models.reward_models import (
    SolutionEvaluation,
    KnowledgeEntry,
    KnowledgeEntryType,
    VersionInfo,
    RewardTransaction
)
from ..database.knowledge_store import KnowledgeStore
from ..llms.llm import get_llm
from ..config.configuration import get_config


logger = logging.getLogger(__name__)


class KnowledgeManagerAgent:
    """知识管理智能体类"""
    
    def __init__(self):
        """初始化知识管理智能体"""
        self.config = get_config()
        self.llm = get_llm()
        self.knowledge_store = KnowledgeStore()
        
    async def store_solution(self, solution: ImplementationSolution, reward_decision: RewardDecision) -> bool:
        """存储实现方案"""
        try:
            logger.info(f"存储实现方案: {solution.solution_id}")
            
            # 更新方案的奖励决策
            solution.reward_decision = reward_decision
            solution.updated_at = datetime.now()
            
            # 根据奖励决策处理
            if reward_decision == RewardDecision.ACCEPTED:
                await self._handle_accepted_solution(solution)
            elif reward_decision == RewardDecision.REJECTED:
                await self._handle_rejected_solution(solution)
            else:
                await self._handle_pending_solution(solution)
            
            # 存储到数据库
            await self.knowledge_store.store_solution(solution)
            
            # 记录奖励交易
            await self._record_reward_transaction(solution, reward_decision)
            
            logger.info(f"方案存储完成: {solution.solution_id}, 决策: {reward_decision}")
            return True
            
        except Exception as e:
            logger.error(f"存储方案失败: {e}")
            return False
    
    async def search_similar_solutions(self, request: DevelopmentRequest) -> List[ImplementationSolution]:
        """搜索相似的实现方案"""
        try:
            logger.info(f"搜索相似方案: {request.title}")
            
            # 生成搜索关键词
            keywords = await self._extract_keywords(request)
            
            # 在知识库中搜索
            similar_solutions = await self.knowledge_store.search_solutions(
                keywords=keywords,
                requirements=request.requirements,
                limit=5
            )
            
            # 按相似度排序
            ranked_solutions = await self._rank_solutions_by_similarity(request, similar_solutions)
            
            logger.info(f"找到{len(ranked_solutions)}个相似方案")
            return ranked_solutions
            
        except Exception as e:
            logger.error(f"搜索相似方案失败: {e}")
            return []
    
    async def get_best_practices(self, operation_type: str) -> List[KnowledgeEntry]:
        """获取最佳实践"""
        try:
            logger.info(f"获取最佳实践: {operation_type}")
            
            best_practices = await self.knowledge_store.get_knowledge_entries(
                entry_type=KnowledgeEntryType.BEST_PRACTICE,
                keywords=[operation_type],
                limit=10
            )
            
            # 按质量得分排序
            best_practices.sort(key=lambda x: x.quality_score, reverse=True)
            
            return best_practices
            
        except Exception as e:
            logger.error(f"获取最佳实践失败: {e}")
            return []
    
    async def create_knowledge_entry(self, solution: ImplementationSolution) -> Optional[KnowledgeEntry]:
        """从成功方案创建知识条目"""
        try:
            if solution.reward_decision != RewardDecision.ACCEPTED:
                return None
            
            logger.info(f"创建知识条目: {solution.solution_id}")
            
            # 使用LLM提取知识点
            knowledge_prompt = ChatPromptTemplate.from_template("""
基于以下成功的实现方案，提取可复用的知识点和最佳实践。

方案标题: {title}
方案描述: {description}
操作数量: {operation_count}
成功率: {success_rate}

请提取：
1. 关键的实现模式
2. 可复用的操作序列
3. 重要的注意事项
4. 优化建议

请以JSON格式返回：
{{
    "title": "知识条目标题",
    "description": "知识条目描述",
    "entry_type": "solution_pattern/best_practice/optimization_tip",
    "content": {{
        "patterns": ["模式1", "模式2"],
        "sequences": ["序列1", "序列2"],
        "notes": ["注意事项1", "注意事项2"],
        "optimizations": ["优化1", "优化2"]
    }},
    "keywords": ["关键词1", "关键词2"],
    "tags": ["标签1", "标签2"]
}}
""")
            
            response = await self.llm.ainvoke(
                knowledge_prompt.format_messages(
                    title=solution.title,
                    description=solution.description,
                    operation_count=len(solution.operations),
                    success_rate=solution.success_rate
                )
            )
            
            # 解析知识点
            knowledge_data = self._parse_json_response(response.content)
            
            # 创建知识条目
            entry = KnowledgeEntry(
                title=knowledge_data.get("title", solution.title),
                description=knowledge_data.get("description", solution.description),
                entry_type=KnowledgeEntryType(knowledge_data.get("entry_type", "solution_pattern")),
                content=knowledge_data.get("content", {}),
                related_solution_ids=[solution.solution_id],
                keywords=knowledge_data.get("keywords", []),
                tags=knowledge_data.get("tags", []),
                quality_score=solution.success_rate,
                is_verified=True
            )
            
            # 存储知识条目
            await self.knowledge_store.store_knowledge_entry(entry)
            
            logger.info(f"知识条目创建完成: {entry.entry_id}")
            return entry
            
        except Exception as e:
            logger.error(f"创建知识条目失败: {e}")
            return None
    
    async def rollback_solution(self, solution_id: str) -> bool:
        """回滚实现方案"""
        try:
            logger.info(f"回滚实现方案: {solution_id}")
            
            # 获取方案
            solution = await self.knowledge_store.get_solution(solution_id)
            if not solution:
                logger.error(f"未找到方案: {solution_id}")
                return False
            
            # 创建回滚版本
            rollback_version = VersionInfo(
                entity_id=solution_id,
                entity_type="implementation_solution",
                version_number=solution.version + 1,
                change_summary="回滚操作",
                change_details={"reason": "用户拒绝方案"},
                version_data=solution.dict(),
                is_rollback=True
            )
            
            # 存储版本信息
            await self.knowledge_store.store_version(rollback_version)
            
            # 更新方案状态
            solution.reward_decision = RewardDecision.REJECTED
            solution.success_rate = max(0.0, solution.success_rate - 0.1)
            solution.updated_at = datetime.now()
            
            # 更新存储
            await self.knowledge_store.update_solution(solution)
            
            logger.info(f"方案回滚完成: {solution_id}")
            return True
            
        except Exception as e:
            logger.error(f"回滚方案失败: {e}")
            return False
    
    async def evaluate_solution(self, solution: ImplementationSolution, evaluator_feedback: Dict[str, Any]) -> SolutionEvaluation:
        """评估实现方案"""
        try:
            logger.info(f"评估实现方案: {solution.solution_id}")
            
            # 创建评估对象
            evaluation = SolutionEvaluation(
                solution_id=solution.solution_id,
                evaluator_type="human",
                evaluator_id=evaluator_feedback.get("evaluator_id", "unknown")
            )
            
            # 设置评估分数
            evaluation.functionality_score = evaluator_feedback.get("functionality_score", 0.0)
            evaluation.code_quality_score = evaluator_feedback.get("code_quality_score", 0.0)
            evaluation.performance_score = evaluator_feedback.get("performance_score", 0.0)
            evaluation.user_satisfaction_score = evaluator_feedback.get("user_satisfaction_score", 0.0)
            
            # 计算综合得分
            criteria = await self.knowledge_store.get_reward_criteria()
            evaluation.calculate_overall_score(criteria)
            
            # 设置详细反馈
            evaluation.detailed_feedback = evaluator_feedback.get("detailed_feedback", {})
            evaluation.strengths = evaluator_feedback.get("strengths", [])
            evaluation.weaknesses = evaluator_feedback.get("weaknesses", [])
            evaluation.improvement_suggestions = evaluator_feedback.get("improvement_suggestions", [])
            
            # 完成评估
            evaluation.status = "completed"
            evaluation.completed_at = datetime.now()
            
            # 存储评估结果
            await self.knowledge_store.store_evaluation(evaluation)
            
            logger.info(f"方案评估完成: {solution.solution_id}, 综合得分: {evaluation.overall_score:.2f}")
            return evaluation
            
        except Exception as e:
            logger.error(f"评估方案失败: {e}")
            return SolutionEvaluation(
                solution_id=solution.solution_id,
                evaluator_type="system",
                status="failed"
            )
    
    async def cleanup_old_solutions(self, retention_days: int = 90) -> int:
        """清理旧的方案"""
        try:
            logger.info(f"清理{retention_days}天前的旧方案")
            
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # 获取需要清理的方案
            old_solutions = await self.knowledge_store.get_solutions_before_date(cutoff_date)
            
            cleaned_count = 0
            for solution in old_solutions:
                # 只清理被拒绝的方案
                if solution.reward_decision == RewardDecision.REJECTED:
                    await self.knowledge_store.delete_solution(solution.solution_id)
                    cleaned_count += 1
            
            logger.info(f"清理完成，删除了{cleaned_count}个旧方案")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理旧方案失败: {e}")
            return 0
    
    async def _handle_accepted_solution(self, solution: ImplementationSolution):
        """处理被接受的方案"""
        # 提高成功率
        solution.success_rate = min(1.0, solution.success_rate + 0.1)
        
        # 创建知识条目
        await self.create_knowledge_entry(solution)
    
    async def _handle_rejected_solution(self, solution: ImplementationSolution):
        """处理被拒绝的方案"""
        # 降低成功率
        solution.success_rate = max(0.0, solution.success_rate - 0.1)
        
        # 记录拒绝原因（如果有的话）
        if solution.validation_result:
            solution.validation_result.issues.append("方案被用户拒绝")
    
    async def _handle_pending_solution(self, solution: ImplementationSolution):
        """处理待定的方案"""
        # 保持当前状态，等待进一步评估
        pass
    
    async def _record_reward_transaction(self, solution: ImplementationSolution, decision: RewardDecision):
        """记录奖励交易"""
        try:
            transaction = RewardTransaction(
                solution_id=solution.solution_id,
                evaluation_id="",  # 如果有评估ID的话
                reward_type=decision.value,
                reward_reason=f"方案{decision.value}",
                status="processed",
                processed_at=datetime.now()
            )
            
            # 根据决策设置奖励积分
            if decision == RewardDecision.ACCEPTED:
                transaction.reward_points = 100
            elif decision == RewardDecision.REJECTED:
                transaction.reward_points = -50
            else:
                transaction.reward_points = 0
            
            await self.knowledge_store.store_reward_transaction(transaction)
            
        except Exception as e:
            logger.error(f"记录奖励交易失败: {e}")
    
    async def _extract_keywords(self, request: DevelopmentRequest) -> List[str]:
        """提取搜索关键词"""
        try:
            # 使用LLM提取关键词
            keyword_prompt = ChatPromptTemplate.from_template("""
从以下开发需求中提取关键词，用于搜索相似的实现方案。

标题: {title}
描述: {description}
要求: {requirements}

请提取最重要的关键词，包括：
1. 功能类型
2. 技术术语
3. 业务领域
4. 操作类型

请以JSON格式返回：
{{
    "keywords": ["关键词1", "关键词2", "关键词3"]
}}
""")
            
            response = await self.llm.ainvoke(
                keyword_prompt.format_messages(
                    title=request.title,
                    description=request.description,
                    requirements=", ".join(request.requirements)
                )
            )
            
            result = self._parse_json_response(response.content)
            return result.get("keywords", [])
            
        except Exception as e:
            logger.error(f"提取关键词失败: {e}")
            return [request.title]
    
    async def _rank_solutions_by_similarity(self, request: DevelopmentRequest, solutions: List[ImplementationSolution]) -> List[ImplementationSolution]:
        """按相似度排序方案"""
        try:
            # 简化的相似度计算
            scored_solutions = []
            
            for solution in solutions:
                similarity_score = self._calculate_similarity(request, solution)
                scored_solutions.append((solution, similarity_score))
            
            # 按相似度排序
            scored_solutions.sort(key=lambda x: x[1], reverse=True)
            
            return [solution for solution, _ in scored_solutions]
            
        except Exception as e:
            logger.error(f"排序方案失败: {e}")
            return solutions
    
    def _calculate_similarity(self, request: DevelopmentRequest, solution: ImplementationSolution) -> float:
        """计算相似度"""
        try:
            # 简化的相似度计算
            title_similarity = self._text_similarity(request.title, solution.title)
            desc_similarity = self._text_similarity(request.description, solution.description)
            
            # 加权平均
            similarity = (title_similarity * 0.6 + desc_similarity * 0.4)
            
            # 考虑成功率
            similarity *= solution.success_rate
            
            return similarity
            
        except Exception as e:
            logger.error(f"计算相似度失败: {e}")
            return 0.0
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        try:
            # 简化的文本相似度计算
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            if len(union) == 0:
                return 0.0
            
            return len(intersection) / len(union)
            
        except Exception as e:
            logger.error(f"计算文本相似度失败: {e}")
            return 0.0
    
    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
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
            logger.warning(f"解析JSON响应失败: {e}")
            return {}


# 创建全局知识管理智能体实例
knowledge_manager_agent = KnowledgeManagerAgent()
