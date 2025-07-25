#!/usr/bin/env python3
"""
测试低代码平台API的简单脚本
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8000"

def test_low_code_develop():
    """测试低代码开发API"""
    print("🚀 测试低代码开发API...")
    
    # 准备测试数据
    test_request = {
        "title": "用户管理表单",
        "description": "创建一个简单的用户信息管理表单",
        "requirements": [
            "用户名输入框",
            "邮箱输入框", 
            "电话号码输入框",
            "提交按钮",
            "重置按钮"
        ],
        "priority": 2
    }
    
    try:
        # 发送开发请求
        print("📤 发送开发请求...")
        response = requests.post(
            f"{BASE_URL}/api/low-code/develop",
            json=test_request,
            timeout=60
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 开发请求成功!")
            print(f"📋 方案ID: {result.get('solution_id', 'N/A')}")
            print(f"📝 方案标题: {result.get('title', 'N/A')}")
            print(f"🔧 操作数量: {result.get('operations_count', 0)}")
            print(f"📈 成功率: {result.get('success_rate', 0):.2f}")
            print(f"🎯 奖励决策: {result.get('reward_decision', 'N/A')}")
            return result.get('solution_id')
        else:
            print(f"❌ 开发请求失败: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("⏰ 请求超时")
        return None
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None

def test_validate_solution(solution_id):
    """测试方案验证API"""
    if not solution_id:
        print("⚠️ 没有方案ID，跳过验证测试")
        return
        
    print(f"\n🔍 测试方案验证API (方案ID: {solution_id})...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/low-code/validate",
            params={"solution_id": solution_id},
            timeout=30
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 验证请求成功!")
            print(f"✔️ 验证结果: {'通过' if result.get('is_valid') else '失败'}")
            print(f"📈 验证得分: {result.get('score', 0):.2f}")
            print(f"🔧 问题数量: {len(result.get('issues', []))}")
            print(f"💡 建议数量: {len(result.get('suggestions', []))}")
        else:
            print(f"❌ 验证请求失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 验证请求异常: {e}")

def test_reward_decision(solution_id):
    """测试奖励决策API"""
    if not solution_id:
        print("⚠️ 没有方案ID，跳过奖励决策测试")
        return
        
    print(f"\n🏆 测试奖励决策API (方案ID: {solution_id})...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/low-code/reward",
            params={
                "solution_id": solution_id,
                "decision": "accepted"
            },
            timeout=30
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 奖励决策成功!")
            print(f"🎯 决策结果: {result.get('decision', 'N/A')}")
            print(f"💬 消息: {result.get('message', 'N/A')}")
        else:
            print(f"❌ 奖励决策失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 奖励决策异常: {e}")

def test_list_solutions():
    """测试方案列表API"""
    print(f"\n📋 测试方案列表API...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/low-code/solutions",
            params={"limit": 10, "offset": 0},
            timeout=30
        )
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 方案列表获取成功!")
            print(f"📊 总数量: {result.get('total', 0)}")
            print(f"📋 当前页数量: {len(result.get('solutions', []))}")
        else:
            print(f"❌ 方案列表获取失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 方案列表请求异常: {e}")

def test_server_health():
    """测试服务器健康状态"""
    print("🏥 测试服务器健康状态...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/config", timeout=10)
        
        if response.status_code == 200:
            print("✅ 服务器运行正常!")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 无法连接到服务器: {e}")
        return False

def main():
    """主测试函数"""
    print("🎯 开始测试低代码平台智能体系统API")
    print("=" * 50)
    
    # 1. 测试服务器健康状态
    if not test_server_health():
        print("\n❌ 服务器不可用，退出测试")
        return
    
    print("\n" + "=" * 50)
    
    # 2. 测试低代码开发API
    solution_id = test_low_code_develop()
    
    # 3. 测试验证API
    test_validate_solution(solution_id)
    
    # 4. 测试奖励决策API
    test_reward_decision(solution_id)
    
    # 5. 测试方案列表API
    test_list_solutions()
    
    print("\n" + "=" * 50)
    print("🎉 API测试完成!")

if __name__ == "__main__":
    main()
