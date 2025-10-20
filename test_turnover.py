"""
换手率计算功能测试脚本
用于验证换手率计算逻辑是否正确
"""

import pandas as pd
import numpy as np
from rolling_backtest import calc_turnover_rate

# 创建模拟的portfolios数据
def create_mock_portfolios():
    """创建模拟的组合数据用于测试"""
    portfolios = {}
    
    # 组合0的换手率记录
    portfolios[0] = {
        "turnover_records": {
            pd.Timestamp("2020-01-15"): np.nan,  # 首次建仓
            pd.Timestamp("2020-01-20"): 0.6,     # 60%换手
            pd.Timestamp("2020-01-25"): 0.4,     # 40%换手
            pd.Timestamp("2020-01-30"): 0.5,     # 50%换手
        }
    }
    
    # 组合1的换手率记录
    portfolios[1] = {
        "turnover_records": {
            pd.Timestamp("2020-01-16"): np.nan,  # 首次建仓
            pd.Timestamp("2020-01-21"): 0.7,     # 70%换手
            pd.Timestamp("2020-01-26"): 0.3,     # 30%换手
        }
    }
    
    # 组合2的换手率记录
    portfolios[2] = {
        "turnover_records": {
            pd.Timestamp("2020-01-17"): np.nan,  # 首次建仓
            pd.Timestamp("2020-01-22"): 0.8,     # 80%换手
        }
    }
    
    return portfolios

def test_calc_turnover_rate():
    """测试换手率计算函数"""
    print("=" * 60)
    print("换手率计算功能测试")
    print("=" * 60)
    
    # 创建模拟数据
    portfolios = create_mock_portfolios()
    portfolio_count = 3
    
    # 计算换手率
    print("\n1. 计算换手率...")
    turnover_df = calc_turnover_rate(portfolios, portfolio_count)
    
    # 显示结果
    print("\n2. 换手率DataFrame:")
    print(turnover_df)
    
    # 显示统计信息
    print("\n3. 换手率统计信息:")
    print("\n平均换手率:")
    print(turnover_df.mean())
    
    print("\n换手率标准差:")
    print(turnover_df.std())
    
    print("\n最大换手率:")
    print(turnover_df.max())
    
    print("\n最小换手率:")
    print(turnover_df.min())
    
    # 验证数据结构
    print("\n4. 数据结构验证:")
    print(f"DataFrame形状: {turnover_df.shape}")
    print(f"列名: {turnover_df.columns.tolist()}")
    print(f"索引名称: {turnover_df.index.name}")
    print(f"日期范围: {turnover_df.index.min()} 到 {turnover_df.index.max()}")
    
    # 保存测试结果
    output_path = "test_turnover_output.csv"
    turnover_df.to_csv(output_path)
    print(f"\n5. 测试结果已保存至: {output_path}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_calc_turnover_rate()
