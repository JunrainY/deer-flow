# 低代码平台智能体系统

基于DeerFlow架构的低代码平台自动化开发系统，通过多智能体协作实现低代码功能的自动化开发、验证和知识管理。

## 系统概述

本系统包含以下核心组件：

### 智能体
- **低代码开发智能体** (`low_code_developer.py`): 负责分析需求并自动在低代码平台中实现功能
- **功能验证智能体** (`function_validator.py`): 负责验证实现的功能是否正常工作
- **知识管理智能体** (`knowledge_manager.py`): 负责管理实现方案的存储、检索和奖励机制

### 工具
- **浏览器自动化工具** (`playwright_automation.py`): 基于Playwright的浏览器自动化操作
- **视觉识别工具** (`visual_recognition.py`): 基于OpenAI Vision API的页面分析和元素识别
- **低代码平台操作工具** (`low_code_operations.py`): 封装低代码平台的核心操作

### 工作流
- **低代码开发工作流** (`low_code_workflow.py`): 整合多个智能体的协作流程

## 快速开始

### 1. 环境配置

首先配置环境变量：

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

需要配置的关键变量：

```bash
# 低代码平台配置
LOW_CODE_PLATFORM_URL=https://your-low-code-platform.com
LOW_CODE_USERNAME=your_username
LOW_CODE_PASSWORD=your_password

# 视觉大模型配置
VISION_MODEL_API_KEY=sk-xxx
VISION_MODEL_ENDPOINT=https://api.openai.com/v1

# 数据库配置
KNOWLEDGE_DB_URL=postgresql://user:pass@localhost/knowledge
```

### 2. 安装依赖

```bash
# 安装Python依赖
uv install

# 安装Playwright浏览器
uv run playwright install chromium
```

### 3. 启动服务

```bash
# 启动DeerFlow服务器
uv run python main.py
```

### 4. 使用API

#### 开发低代码功能

```bash
curl -X POST http://localhost:8000/api/low-code/develop \
  -H "Content-Type: application/json" \
  -d '{
    "title": "用户管理表单",
    "description": "创建用户信息管理表单",
    "requirements": [
      "用户名输入框",
      "邮箱输入框",
      "提交按钮"
    ],
    "priority": 2
  }'
```

#### 验证实现方案

```bash
curl -X POST http://localhost:8000/api/low-code/validate \
  -H "Content-Type: application/json" \
  -d '{"solution_id": "your-solution-id"}'
```

#### 提交奖励决策

```bash
curl -X POST http://localhost:8000/api/low-code/reward \
  -H "Content-Type: application/json" \
  -d '{
    "solution_id": "your-solution-id",
    "decision": "accepted"
  }'
```

## 系统架构

### 数据模型

系统使用以下核心数据模型：

- `DevelopmentRequest`: 开发需求
- `ImplementationSolution`: 实现方案
- `LowCodeOperation`: 低代码操作
- `ValidationResult`: 验证结果
- `KnowledgeEntry`: 知识条目

### 工作流程

1. **需求分析**: 分析用户提交的开发需求
2. **知识搜索**: 搜索相似的历史实现方案
3. **方案开发**: 使用低代码开发智能体实现功能
4. **功能验证**: 使用验证智能体测试实现结果
5. **方案审查**: 人工或自动审查方案质量
6. **知识更新**: 将成功方案存储到知识库

### 奖励机制

系统实现了完整的奖励机制：

- **接受方案**: 提高成功率，创建知识条目
- **拒绝方案**: 降低成功率，触发回滚
- **待定方案**: 等待进一步评估

## 配置说明

### 低代码平台配置

编辑 `config/low_code_config.yaml`:

```yaml
LOW_CODE_PLATFORM:
  base_url: "https://your-platform.com"
  modules:
    data_modeling:
      enabled: true
      entry_selector: "[data-module='data-modeling']"
    form_design:
      enabled: true
      entry_selector: "[data-module='form-design']"
```

### 浏览器配置

编辑 `config/browser_config.yaml`:

```yaml
BROWSER_LAUNCH:
  browser_type: "chromium"
  launch_options:
    headless: false
    slow_mo: 100
```

## 测试

### 运行单元测试

```bash
uv run pytest tests/test_low_code_agents.py -v
```

### 运行集成测试

```bash
# 启动测试环境
uv run python -m pytest tests/ -v --cov=src/agents --cov=src/tools
```

### 手动测试

1. 启动服务器
2. 访问 http://localhost:8000/docs 查看API文档
3. 使用Swagger UI测试各个接口

## 故障排除

### 常见问题

1. **浏览器启动失败**
   - 检查Playwright是否正确安装
   - 确认系统依赖是否完整

2. **视觉识别失败**
   - 检查OpenAI API密钥是否正确
   - 确认网络连接正常

3. **低代码平台连接失败**
   - 检查平台URL和凭据
   - 确认平台可访问性

### 调试模式

启用调试模式：

```bash
export LOW_CODE_AGENT_DEBUG=true
uv run python main.py
```

查看详细日志：

```bash
tail -f logs/low_code_agent.log
```

## 扩展开发

### 添加新的操作类型

1. 在 `OperationType` 枚举中添加新类型
2. 在 `low_code_operations.py` 中实现对应方法
3. 更新配置文件中的模块配置

### 集成新的低代码平台

1. 创建平台特定的操作工具
2. 更新配置文件
3. 实现平台特定的元素选择器

### 优化视觉识别

1. 调整提示词模板
2. 优化图像预处理
3. 实现缓存机制

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

## 许可证

MIT License

## 联系方式

如有问题或建议，请提交Issue或联系开发团队。
