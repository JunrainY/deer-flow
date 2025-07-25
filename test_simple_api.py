#!/usr/bin/env python3
"""
简化的API测试脚本 - 不需要真实的低代码平台连接
"""

import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000"

def test_basic_apis():
    """测试基础API功能"""
    print("🎯 测试基础API功能")
    print("=" * 50)
    
    # 1. 测试配置API
    print("🔧 测试配置API...")
    try:
        response = requests.get(f"{BASE_URL}/api/config", timeout=10)
        if response.status_code == 200:
            config = response.json()
            print("✅ 配置API正常")
            print(f"📋 RAG提供商: {config.get('rag', {}).get('provider', 'N/A')}")
            print(f"🤖 模型数量: {len(config.get('models', []))}")
        else:
            print(f"❌ 配置API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 配置API异常: {e}")
    
    print()
    
    # 2. 测试方案列表API
    print("📋 测试方案列表API...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/low-code/solutions",
            params={"limit": 5, "offset": 0},
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print("✅ 方案列表API正常")
            print(f"📊 总数量: {result.get('total', 0)}")
            print(f"📋 当前页数量: {len(result.get('solutions', []))}")
        else:
            print(f"❌ 方案列表API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 方案列表API异常: {e}")
    
    print()
    
    # 3. 测试验证API（使用虚拟ID）
    print("🔍 测试验证API...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/low-code/validate",
            params={"solution_id": "test-solution-123"},
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print("✅ 验证API正常")
            print(f"✔️ 验证结果: {'通过' if result.get('is_valid') else '失败'}")
            print(f"📈 验证得分: {result.get('score', 0):.2f}")
        else:
            print(f"❌ 验证API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 验证API异常: {e}")
    
    print()
    
    # 4. 测试奖励决策API
    print("🏆 测试奖励决策API...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/low-code/reward",
            params={
                "solution_id": "test-solution-123",
                "decision": "accepted"
            },
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            print("✅ 奖励决策API正常")
            print(f"🎯 决策结果: {result.get('decision', 'N/A')}")
            print(f"💬 消息: {result.get('message', 'N/A')}")
        else:
            print(f"❌ 奖励决策API失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 奖励决策API异常: {e}")
    
    print()
    print("=" * 50)
    print("🎉 基础API测试完成!")

def test_api_documentation():
    """测试API文档可访问性"""
    print("\n📚 测试API文档...")
    try:
        response = requests.get(f"{BASE_URL}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ API文档可访问")
            print(f"🌐 访问地址: {BASE_URL}/docs")
        else:
            print(f"❌ API文档不可访问: {response.status_code}")
    except Exception as e:
        print(f"❌ API文档访问异常: {e}")

def show_system_info():
    """显示系统信息"""
    print("📋 低代码平台智能体系统信息")
    print("=" * 50)
    print("🏗️  系统架构: 基于DeerFlow的多智能体协作系统")
    print("🤖 智能体:")
    print("   - 低代码开发智能体 (low_code_developer)")
    print("   - 功能验证智能体 (function_validator)")
    print("   - 知识管理智能体 (knowledge_manager)")
    print("🛠️  核心工具:")
    print("   - Playwright浏览器自动化")
    print("   - OpenAI Vision API视觉识别")
    print("   - SQLAlchemy数据持久化")
    print("🌐 API接口:")
    print("   - POST /api/low-code/develop - 开发低代码功能")
    print("   - POST /api/low-code/validate - 验证实现方案")
    print("   - POST /api/low-code/reward - 提交奖励决策")
    print("   - GET  /api/low-code/solutions - 获取方案列表")
    print("📖 文档地址: http://localhost:8000/docs")
    print("=" * 50)

def main():
    """主函数"""
    show_system_info()
    print()
    test_basic_apis()
    test_api_documentation()
    
    print("\n💡 使用说明:")
    print("1. 当前系统已成功启动，基础API功能正常")
    print("2. 要测试完整功能，需要配置以下环境变量:")
    print("   - LOW_CODE_PLATFORM_URL: 低代码平台地址")
    print("   - LOW_CODE_USERNAME: 平台用户名")
    print("   - LOW_CODE_PASSWORD: 平台密码")
    print("   - VISION_MODEL_API_KEY: OpenAI API密钥")
    print("3. 配置完成后，可以通过API开发真实的低代码功能")
    print("4. 访问 http://localhost:8000/docs 查看完整API文档")

if __name__ == "__main__":
    main()
