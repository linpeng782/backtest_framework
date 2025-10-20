# 换手率计算功能使用说明

## 功能概述

换手率计算功能已集成到滚动回测框架中，可以自动计算每个组合在每次调仓时的换手率。

## 换手率定义

换手率 = (上次持仓股票数 - 本次与上次的交集股票数) / 上次持仓股票数

例如：
- 上次持仓：['股票A', '股票B', '股票C', '股票D', '股票E']  (5只)
- 本次持仓：['股票A', '股票C', '股票F', '股票G', '股票H']  (5只)
- 交集：['股票A', '股票C']  (2只)
- 换手率 = (5 - 2) / 5 = 0.6 (60%)

## 使用方法

### 方法1：通过BacktestFramework自动计算（推荐）

```python
from backtest_framework import BacktestFramework

# 创建回测框架实例
framework = BacktestFramework(
    signal_file="your_signal.csv",
    start_date="2020-01-01",
    end_date="2025-01-01",
    rank_n=30,
    rebalance_frequency=5,
    portfolio_count=5,
    data_dir="/path/to/data",
    cache_dir="/path/to/cache",
    output_dir="/path/to/output"
)

# 运行回测（会自动计算换手率并保存）
framework.run_backtest()

# 换手率数据会自动保存到：output_dir/turnover_rate.csv
```

### 方法2：手动调用

```python
from rolling_backtest import rolling_backtest, calc_turnover_rate
import pandas as pd

# 执行回测
account_result, portfolios, portfolio_count = rolling_backtest(
    portfolio_weights=portfolio_weights,
    bars_df=vwap_df,
    trading_days_df=trading_days,
    portfolio_count=5,
    rebalance_frequency=5,
)

# 计算换手率
turnover_df = calc_turnover_rate(portfolios, portfolio_count)

# 保存换手率数据
turnover_df.to_csv("turnover_rate.csv")

# 查看换手率统计
print("平均换手率:")
print(turnover_df.mean())
print("\n换手率标准差:")
print(turnover_df.std())
```

## 输出格式

换手率数据保存为CSV文件，格式如下：

| 调仓日期 | G0 | G1 | G2 | G3 | G4 |
|---------|----|----|----|----|-----|
| 2020-01-15 | NaN | NaN | NaN | NaN | NaN |
| 2020-01-20 | 0.65 | NaN | NaN | NaN | NaN |
| 2020-01-25 | 0.58 | 0.72 | NaN | NaN | NaN |
| ... | ... | ... | ... | ... | ... |

说明：
- 每一列代表一个组合（G0, G1, G2...）
- 每一行代表一个调仓日期
- NaN表示该组合在该日期首次建仓（无换手率）
- 数值表示换手率（0-1之间，1表示100%换手）

## 注意事项

1. 首次建仓时换手率为NaN（因为没有上一次持仓可比较）
2. 换手率计算基于股票名称集合，不考虑持仓数量变化
3. 换手率越高，表示组合调整幅度越大，交易成本可能越高
4. 可以通过平均换手率评估策略的稳定性

## 数据结构说明

在`rolling_backtest`函数中，每个组合的数据结构如下：

```python
portfolios[i] = {
    "holdings": pd.Series(dtype=float),      # 当前持仓股票及数量
    "cash": 0.0,                             # 现金余额
    "start_date": None,                      # 建仓日期
    "expire_date": None,                     # 到期日期
    "is_active": False,                      # 是否激活
    "previous_stocks": set(),                # 上一次持仓的股票集合
    "turnover_records": {},                  # 换手率记录 {日期: 换手率}
}
```

其中：
- `previous_stocks`: 存储上一次调仓时的股票名称集合
- `turnover_records`: 字典，键为调仓日期，值为该日期的换手率
