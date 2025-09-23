# 量化回测框架 (Backtesting OOP)

一个基于面向对象设计的量化回测框架，专门用于股票投资策略的回测分析。

## 项目特点

- **面向对象设计**：模块化架构，易于扩展和维护
- **灵活的信号处理**：支持多种信号文件格式
- **完整的回测功能**：包含滚动回测、性能分析等
- **简洁的配置管理**：使用YAML配置文件，易于修改参数
- **数据代码分离**：遵循最佳实践，数据存储在独立目录

## 项目结构

```
backtesting_oop/
├── README.md                    # 项目说明文档
├── backtest_config.yaml         # 回测配置文件
├── requirements.txt             # 依赖包列表
├── __init__.py                  # 包初始化文件
├── signal_reader.py             # 信号文件读取模块
├── backtest_framework.py        # 回测框架核心模块
├── backtest_rolling_flexible.py # 灵活滚动回测模块
├── performance_analyzer.py      # 性能分析模块
├── get_buy_signal.py           # 买入信号处理模块
├── feval_backtest.py           # 回测执行脚本
└── test_config.py              # 配置测试脚本
```

## 安装依赖

```bash
# 激活虚拟环境
conda activate peterdidi

# 安装依赖包
pip install -r requirements.txt
```

## 快速开始

### 1. 配置参数

编辑 `backtest_config.yaml` 文件，设置您的回测参数：

```yaml
# 信号文件名
signal_file: "your_signal_file"

# 信号目录
data_dir: "/Users/didi/DATA/dnn_model/signal"

# 回测结果保存目录
save_dir: "/Users/didi/DATA/dnn_model/signal"

# 每日选股数量
rank_n: 30

# 组合数量（资金分割份数）
portfolio_count: 5

# 调仓频率
rebalance_frequency: "daily"

# 基准指数
benchmark: "000852.XSHG"  # 中证1000
```

### 2. 运行回测

```bash
python feval_backtest.py
```

## 主要功能模块

### 信号处理 (signal_reader.py)
- 支持多种信号文件格式
- 自动检测文件格式并解析
- 提供数据转换和验证功能

### 回测框架 (backtest_framework.py)
- 完整的回测流程管理
- 支持多种调仓策略
- 灵活的参数配置

### 性能分析 (performance_analyzer.py)
- 全面的回测结果分析
- 风险指标计算
- 可视化图表生成

### 滚动回测 (backtest_rolling_flexible.py)
- 支持滚动回测策略
- 灵活的组合管理
- 多种调仓频率支持

## 配置说明

### 基本参数
- `signal_file`: 信号文件名
- `data_dir`: 数据目录路径
- `save_dir`: 结果保存目录

### 策略参数
- `rank_n`: 每日选股数量
- `portfolio_count`: 组合数量（资金分割份数）
- `rebalance_frequency`: 调仓频率（daily/weekly/monthly）
- `benchmark`: 基准指数代码

### 输出设置
- `save_results`: 是否保存结果到文件
- `output_dir`: 输出目录名称

## 数据格式

### 信号文件格式
支持两种格式：

1. **带排名格式**：`日期 股票代码 排名`
2. **不带排名格式**：`日期_股票代码`

### 输出结果
- 账户历史记录 (CSV)
- 性能指标汇总 (CSV)
- 投资组合权重 (CSV)

## 开发指南

### 环境要求
- Python 3.7+
- pandas, numpy, matplotlib等数据科学包
- PyYAML用于配置文件解析

### 代码规范
- 所有注释和文档使用中文
- 遵循数据代码分离原则
- 优先使用向量化操作，避免循环

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 联系方式

如有问题或建议，请通过以下方式联系：
- 创建 Issue
- 发送邮件

---

**注意**：运行任何脚本前需要先激活虚拟环境：`conda activate peterdidi`
