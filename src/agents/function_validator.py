"""
功能验证智能体

自动化功能测试和修复建议智能体
负责验证低代码平台实现的功能是否正常工作
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import json

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from ..models.low_code_models import (
    ImplementationSolution,
    ValidationResult,
    LowCodeOperation,
    OperationType,
    ActionType,
    VisualAnalysisResult
)
from ..tools.playwright_automation import PlaywrightAutomation
from ..tools.visual_recognition import VisualRecognition
from ..llms.llm import get_llm
from ..config.configuration import get_config


logger = logging.getLogger(__name__)


class ValidationState(BaseModel):
    """验证状态模型"""
    solution: Optional[ImplementationSolution] = None
    validation_result: Optional[ValidationResult] = None
    test_scenarios: List[Dict[str, Any]] = Field(default_factory=list)
    current_test_index: int = 0
    test_results: List[Dict[str, Any]] = Field(default_factory=list)
    issues_found: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    error_count: int = 0
    max_errors: int = 3


class FunctionValidatorAgent:
    """功能验证智能体类"""
    
    def __init__(self):
        """初始化功能验证智能体"""
        self.config = get_config()
        self.llm = get_llm()
        self.browser = PlaywrightAutomation()
        self.vision = VisualRecognition()
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        """构建验证工作流图"""
        graph = StateGraph(ValidationState)
        
        # 添加节点
        graph.add_node("analyze_solution", self._analyze_solution)
        graph.add_node("generate_test_scenarios", self._generate_test_scenarios)
        graph.add_node("setup_test_environment", self._setup_test_environment)
        graph.add_node("execute_tests", self._execute_tests)
        graph.add_node("analyze_test_results", self._analyze_test_results)
        graph.add_node("generate_suggestions", self._generate_suggestions)
        graph.add_node("finalize_validation", self._finalize_validation)
        
        # 设置入口点
        graph.set_entry_point("analyze_solution")
        
        # 添加边
        graph.add_edge("analyze_solution", "generate_test_scenarios")
        graph.add_edge("generate_test_scenarios", "setup_test_environment")
        graph.add_edge("setup_test_environment", "execute_tests")
        graph.add_conditional_edges(
            "execute_tests",
            self._should_continue_testing,
            {
                "continue": "execute_tests",
                "analyze": "analyze_test_results",
                "error": "finalize_validation"
            }
        )
        graph.add_edge("analyze_test_results", "generate_suggestions")
        graph.add_edge("generate_suggestions", "finalize_validation")
        graph.add_edge("finalize_validation", END)
        
        return graph.compile()
    
    async def validate(self, solution: ImplementationSolution) -> ValidationResult:
        """验证实现方案"""
        try:
            # 初始化验证状态
            initial_state = ValidationState(
                solution=solution,
                validation_result=ValidationResult(
                    is_valid=False,
                    validator_agent="function_validator"
                )
            )
            
            # 执行验证工作流
            final_state = await self.graph.ainvoke(initial_state)
            
            return final_state.validation_result
            
        except Exception as e:
            logger.error(f"验证过程中出错: {e}")
            return ValidationResult(
                is_valid=False,
                issues=[f"验证失败: {str(e)}"],
                validator_agent="function_validator"
            )
    
    async def _analyze_solution(self, state: ValidationState) -> ValidationState:
        """分析实现方案"""
        try:
            logger.info("分析实现方案")
            
            solution = state.solution
            
            # 使用LLM分析方案
            analysis_prompt = ChatPromptTemplate.from_template("""
你是一个低代码平台功能验证专家。请分析以下实现方案，确定需要验证的功能点。

方案标题: {title}
方案描述: {description}
操作数量: {operation_count}
操作类型: {operation_types}

请分析：
1. 主要功能点
2. 关键验证项
3. 可能的风险点
4. 性能考虑因素

请以JSON格式返回分析结果：
{{
    "main_functions": ["功能1", "功能2"],
    "key_validations": ["验证项1", "验证项2"],
    "risk_points": ["风险1", "风险2"],
    "performance_factors": ["因素1", "因素2"]
}}
""")
            
            operation_types = list(set(op.operation_type.value for op in solution.operations))
            
            response = await self.llm.ainvoke(
                analysis_prompt.format_messages(
                    title=solution.title,
                    description=solution.description,
                    operation_count=len(solution.operations),
                    operation_types=", ".join(operation_types)
                )
            )
            
            # 解析分析结果
            analysis_result = self._parse_json_response(response.content)
            
            # 存储分析结果
            state.validation_result.test_results["analysis"] = analysis_result
            
            logger.info(f"方案分析完成: {analysis_result}")
            return state
            
        except Exception as e:
            logger.error(f"分析方案失败: {e}")
            state.error_count += 1
            return state
    
    async def _generate_test_scenarios(self, state: ValidationState) -> ValidationState:
        """生成测试场景"""
        try:
            logger.info("生成测试场景")
            
            analysis = state.validation_result.test_results.get("analysis", {})
            main_functions = analysis.get("main_functions", [])
            
            # 使用LLM生成测试场景
            scenario_prompt = ChatPromptTemplate.from_template("""
基于功能分析结果，请生成详细的测试场景。

主要功能: {functions}
关键验证项: {validations}
风险点: {risks}

请为每个功能生成测试场景，包括：
1. 基本功能测试
2. 边界条件测试
3. 错误处理测试
4. 性能测试

请以JSON格式返回测试场景：
{{
    "scenarios": [
        {{
            "name": "测试场景名称",
            "type": "basic_functionality/edge_cases/error_handling/performance",
            "description": "测试描述",
            "steps": ["步骤1", "步骤2"],
            "expected_result": "预期结果",
            "validation_criteria": ["标准1", "标准2"]
        }}
    ]
}}
""")
            
            response = await self.llm.ainvoke(
                scenario_prompt.format_messages(
                    functions=", ".join(main_functions),
                    validations=", ".join(analysis.get("key_validations", [])),
                    risks=", ".join(analysis.get("risk_points", []))
                )
            )
            
            # 解析测试场景
            scenario_result = self._parse_json_response(response.content)
            state.test_scenarios = scenario_result.get("scenarios", [])
            
            logger.info(f"生成了{len(state.test_scenarios)}个测试场景")
            return state
            
        except Exception as e:
            logger.error(f"生成测试场景失败: {e}")
            state.error_count += 1
            return state
    
    async def _setup_test_environment(self, state: ValidationState) -> ValidationState:
        """设置测试环境"""
        try:
            logger.info("设置测试环境")
            
            # 启动浏览器
            if not await self.browser.start_browser():
                raise Exception("启动浏览器失败")
            
            # 导航到实现的功能页面
            # 这里需要根据实际情况确定功能页面URL
            platform_url = self.config.get("LOW_CODE_PLATFORM", {}).get("base_url", "")
            if platform_url:
                await self.browser.navigate_to_url(platform_url)
            
            logger.info("测试环境设置完成")
            return state
            
        except Exception as e:
            logger.error(f"设置测试环境失败: {e}")
            state.error_count += 1
            return state
    
    async def _execute_tests(self, state: ValidationState) -> ValidationState:
        """执行测试"""
        try:
            if state.current_test_index >= len(state.test_scenarios):
                logger.info("所有测试执行完成")
                return state
            
            current_scenario = state.test_scenarios[state.current_test_index]
            logger.info(f"执行测试 {state.current_test_index + 1}/{len(state.test_scenarios)}: {current_scenario['name']}")
            
            start_time = datetime.now()
            
            # 执行测试步骤
            test_result = await self._execute_test_scenario(current_scenario)
            
            # 记录执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            test_result["execution_time"] = execution_time
            
            # 存储测试结果
            state.test_results.append(test_result)
            
            # 更新性能指标
            if current_scenario["type"] == "performance":
                state.performance_metrics[current_scenario["name"]] = execution_time
            
            # 移动到下一个测试
            state.current_test_index += 1
            
            return state
            
        except Exception as e:
            logger.error(f"执行测试失败: {e}")
            state.error_count += 1
            return state
    
    async def _execute_test_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个测试场景"""
        try:
            test_result = {
                "scenario_name": scenario["name"],
                "scenario_type": scenario["type"],
                "success": False,
                "issues": [],
                "observations": []
            }
            
            # 截图测试前状态
            before_screenshot = await self.browser.take_screenshot(f"test_before_{scenario['name']}.png")
            
            # 执行测试步骤
            for i, step in enumerate(scenario.get("steps", [])):
                try:
                    # 使用视觉识别执行步骤
                    success = await self._execute_test_step(step)
                    if not success:
                        test_result["issues"].append(f"步骤{i+1}执行失败: {step}")
                        break
                except Exception as e:
                    test_result["issues"].append(f"步骤{i+1}出错: {str(e)}")
                    break
            
            # 截图测试后状态
            after_screenshot = await self.browser.take_screenshot(f"test_after_{scenario['name']}.png")
            
            # 使用视觉识别验证结果
            validation_result = await self._validate_test_result(
                scenario,
                before_screenshot,
                after_screenshot
            )
            
            test_result["success"] = validation_result["success"]
            test_result["observations"].extend(validation_result["observations"])
            
            if not validation_result["success"]:
                test_result["issues"].extend(validation_result["issues"])
            
            return test_result
            
        except Exception as e:
            logger.error(f"执行测试场景失败: {e}")
            return {
                "scenario_name": scenario["name"],
                "scenario_type": scenario["type"],
                "success": False,
                "issues": [f"测试执行异常: {str(e)}"],
                "observations": []
            }
    
    async def _execute_test_step(self, step: str) -> bool:
        """执行测试步骤"""
        try:
            # 使用视觉识别找到相关元素
            screenshot_path = await self.browser.take_screenshot()
            suggestions = await self.vision.find_element_suggestions(screenshot_path, step)
            
            if suggestions:
                # 创建操作并执行
                operation = LowCodeOperation(
                    operation_type=OperationType.NAVIGATION,
                    action=ActionType.CLICK,
                    target_element=suggestions[0],
                    parameters={"step_description": step}
                )
                
                return await self.browser.execute_operation(operation)
            else:
                logger.warning(f"未找到步骤对应的元素: {step}")
                return False
                
        except Exception as e:
            logger.error(f"执行测试步骤失败: {e}")
            return False
    
    async def _validate_test_result(self, scenario: Dict[str, Any], before_screenshot: str, after_screenshot: str) -> Dict[str, Any]:
        """验证测试结果"""
        try:
            # 使用视觉识别分析测试结果
            analysis_result = await self.vision.analyze_screenshot(
                after_screenshot,
                f"请验证测试场景'{scenario['name']}'的执行结果是否符合预期: {scenario.get('expected_result', '')}"
            )
            
            # 判断测试是否成功
            success_indicators = [
                "成功",
                "完成",
                "正确",
                "符合预期"
            ]
            
            is_success = any(
                indicator in suggestion.lower()
                for suggestion in analysis_result.suggestions
                for indicator in success_indicators
            )
            
            return {
                "success": is_success and analysis_result.confidence_score > 0.6,
                "observations": analysis_result.suggestions,
                "issues": [] if is_success else ["测试结果不符合预期"]
            }
            
        except Exception as e:
            logger.error(f"验证测试结果失败: {e}")
            return {
                "success": False,
                "observations": [],
                "issues": [f"验证失败: {str(e)}"]
            }

    async def _analyze_test_results(self, state: ValidationState) -> ValidationState:
        """分析测试结果"""
        try:
            logger.info("分析测试结果")

            # 统计测试结果
            total_tests = len(state.test_results)
            successful_tests = sum(1 for result in state.test_results if result["success"])
            failed_tests = total_tests - successful_tests

            # 收集所有问题
            all_issues = []
            for result in state.test_results:
                all_issues.extend(result.get("issues", []))

            state.issues_found = all_issues

            # 计算验证得分
            if total_tests > 0:
                success_rate = successful_tests / total_tests
                state.validation_result.score = success_rate
                state.validation_result.is_valid = success_rate >= 0.7  # 70%通过率认为有效
            else:
                state.validation_result.score = 0.0
                state.validation_result.is_valid = False

            # 设置问题列表
            state.validation_result.issues = all_issues

            # 设置性能指标
            state.validation_result.performance_metrics = state.performance_metrics

            # 计算验证时间
            total_validation_time = sum(
                result.get("execution_time", 0)
                for result in state.test_results
            )
            state.validation_result.validation_time = total_validation_time

            logger.info(f"测试结果分析完成: {successful_tests}/{total_tests} 成功, 得分: {state.validation_result.score:.2f}")
            return state

        except Exception as e:
            logger.error(f"分析测试结果失败: {e}")
            state.error_count += 1
            return state

    async def _generate_suggestions(self, state: ValidationState) -> ValidationState:
        """生成改进建议"""
        try:
            logger.info("生成改进建议")

            if not state.issues_found:
                state.suggestions = ["功能实现良好，无需改进"]
                state.validation_result.suggestions = state.suggestions
                return state

            # 使用LLM生成改进建议
            suggestion_prompt = ChatPromptTemplate.from_template("""
基于测试结果，请为低代码平台功能实现提供改进建议。

发现的问题:
{issues}

测试结果统计:
- 总测试数: {total_tests}
- 成功测试: {successful_tests}
- 失败测试: {failed_tests}
- 成功率: {success_rate:.2f}

请提供具体的改进建议，包括：
1. 问题修复方案
2. 功能优化建议
3. 用户体验改进
4. 性能优化建议

请以JSON格式返回建议：
{{
    "suggestions": [
        "建议1",
        "建议2",
        "建议3"
    ],
    "priority_fixes": [
        "优先修复项1",
        "优先修复项2"
    ],
    "optimization_tips": [
        "优化建议1",
        "优化建议2"
    ]
}}
""")

            total_tests = len(state.test_results)
            successful_tests = sum(1 for result in state.test_results if result["success"])
            failed_tests = total_tests - successful_tests
            success_rate = successful_tests / total_tests if total_tests > 0 else 0

            response = await self.llm.ainvoke(
                suggestion_prompt.format_messages(
                    issues="\n".join(f"- {issue}" for issue in state.issues_found),
                    total_tests=total_tests,
                    successful_tests=successful_tests,
                    failed_tests=failed_tests,
                    success_rate=success_rate
                )
            )

            # 解析建议结果
            suggestion_result = self._parse_json_response(response.content)

            state.suggestions = suggestion_result.get("suggestions", [])
            state.validation_result.suggestions = state.suggestions

            # 存储详细建议
            state.validation_result.test_results["detailed_suggestions"] = suggestion_result

            logger.info(f"生成了{len(state.suggestions)}条改进建议")
            return state

        except Exception as e:
            logger.error(f"生成改进建议失败: {e}")
            state.error_count += 1
            return state

    async def _finalize_validation(self, state: ValidationState) -> ValidationState:
        """完成验证"""
        try:
            logger.info("完成功能验证")

            # 设置验证完成时间
            state.validation_result.created_at = datetime.now()

            # 关闭浏览器
            await self.browser.close_browser()

            # 记录最终结果
            logger.info(f"验证完成 - 有效性: {state.validation_result.is_valid}, "
                       f"得分: {state.validation_result.score:.2f}, "
                       f"问题数: {len(state.validation_result.issues)}")

            return state

        except Exception as e:
            logger.error(f"完成验证失败: {e}")
            state.validation_result.is_valid = False
            state.validation_result.issues.append(f"验证过程异常: {str(e)}")
            return state

    def _should_continue_testing(self, state: ValidationState) -> str:
        """判断是否继续测试"""
        if state.error_count >= state.max_errors:
            return "error"
        elif state.current_test_index >= len(state.test_scenarios):
            return "analyze"
        else:
            return "continue"

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """解析JSON响应"""
        try:
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
            logger.warning(f"解析JSON响应失败: {e}")
            return {}


# 创建全局验证智能体实例
function_validator_agent = FunctionValidatorAgent()
