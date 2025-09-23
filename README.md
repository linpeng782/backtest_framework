# 量化回测框架 (Backtesting OOP)

## 项目结构

```
backtesting_oop/
├── README.md                    # 项目说明文档
├── backtest_config.yaml         # 回测配置文件
├── signal_reader.py             # 信号文件读取和解析模块
├── backtest_framework.py        # 回测框架核心模块
├── rolling_backtest.py          # 12个月滚动持仓回测模块
├── portfolio_weights_gen.py     # 投资组合权重生成模块
├── performance_analyzer.py      # 性能分析和指标计算模块
├── data_utils.py               # 数据处理工具（ST、停牌、涨停过滤）
└── feval_backtest.py           # 简化版回测执行脚本
```

### 1. 配置参数

编辑 `backtest_config.yaml` 文件，设置您的回测参数：

```yaml
# ==================== 基本参数 ====================
# 信号文件名
signal_file: "pred5days_top2k"
  
# 信号目录(需要包含信号文件)
data_dir: "/Users/didi/DATA/dnn_model/signal"

# 回测过程中产生的vwap数据保存目录
save_dir: "/Users/didi/DATA/dnn_model/bars"
 
# ==================== 策略参数 ====================
# 每日选股数量
rank_n: 30

# 组合数量（资金分割份数）
portfolio_count: 5

# 调仓频率（天）
rebalance_frequency: "daily"

# 基准指数
benchmark: "000852.XSHG"  # 中证1000

# ==================== 输出设置 ====================
# 是否保存详细结果到文件
save_results: true

# 回测结果保存目录
output_dir: "backtest_results"

# ==================== 显示设置 ====================
# 是否显示详细日志
verbose: true

# 是否显示进度条
show_progress: true
```

### 3. 查看结果

回测完成后，结果将保存在配置的输出目录中，包括：
- 账户历史记录
- 性能指标汇总
- 投资组合权重变化
- 可视化图表

## 使用示例

### 基本使用流程

1. **准备信号文件**：将您的预测信号文件放在指定的数据目录中
2. **修改配置**：根据您的需求调整`backtest_config.yaml`中的参数
3. **执行回测**：运行`python feval_backtest.py`
4. **分析结果**：查看生成的回测报告和图表

### 自定义开发

如果需要自定义回测逻辑，可以：
- 修改`portfolio_weights_gen.py`中的选股逻辑
- 调整`rolling_backtest.py`中的持仓管理策略
- 扩展`performance_analyzer.py`中的分析指标

## 主要功能模块

### 信号处理 (signal_reader.py)
- 支持多种信号文件格式（带排名/不带排名）
- 自动检测文件格式并解析
- 提供数据转换和验证功能
- 自动解析信号文件的时间范围

### 回测框架 (backtest_framework.py)
- 完整的回测流程管理
- 支持多种调仓策略
- 灵活的参数配置
- 集成数据过滤和风险控制

### 数据处理工具 (data_utils.py)
- ST股票过滤（风险警示标的过滤）
- 停牌股票过滤（无法交易标的过滤）
- 涨停股票过滤（开盘无法买入标的过滤）
- 集成RQData数据源接口

### 滚动回测 (rolling_backtest.py)
- 12个月滚动持仓回测策略
- 精确的持仓计算和资金管理
- 支持最小交易单位约束
- 交易成本预留机制

### 投资组合管理 (portfolio_weights_gen.py)
- 动态选股逻辑（确保每日选出指定数量股票）
- 投资组合权重计算
- 信号处理和过滤集成
- 支持多种权重分配策略

### 性能分析 (performance_analyzer.py)
- 全面的回测结果分析
- 风险指标计算（夏普比率、最大回撤等）
- 可视化图表生成
- 基准对比分析

## 配置说明

### 基本参数
- `signal_file`: 信号文件名（不含扩展名）
- `data_dir`: 信号文件所在目录路径
- `save_dir`: 回测过程中产生的vwap数据保存目录

### 策略参数
- `rank_n`: 每日选股数量
- `portfolio_count`: 组合数量（资金分割份数）
- `rebalance_frequency`: 调仓频率（daily为每日调仓）
- `benchmark`: 基准指数代码（如000852.XSHG为中证1000）

### 输出设置
- `save_results`: 是否保存详细结果到文件
- `output_dir`: 回测结果保存目录名称

### 显示设置
- `verbose`: 是否显示详细日志
- `show_progress`: 是否显示进度条

## 数据格式

### 信号文件格式
支持两种格式：

1. **带排名格式**：`日期 股票代码 排名`
2. **不带排名格式**：`日期_股票代码`

### 输出结果
- 账户历史记录 (CSV)
- 性能指标汇总 (CSV)
- 投资组合权重 (CSV)


