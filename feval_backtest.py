"""
简化版回测执行脚本
读取配置文件并执行回测，简单直接
"""

import sys
import os
import yaml
import time

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest_framework import BacktestFramework
from signal_reader import read_signal_file


def load_config_and_run(config_file="backtest_config.yaml"):
    """加载配置文件并执行回测"""

    # 1. 加载YAML配置文件
    print(f"\n正在加载配置文件...")
    try:
        config_path = os.path.join(os.path.dirname(__file__), config_file)
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        print(f"配置文件加载成功")
    except Exception as e:
        print(f"配置文件加载失败: {e}")
        raise

    # 2. 从信号文件中自动解析日期范围
    print(f"\n正在从信号文件解析日期范围...")
    signal_path = os.path.join(config["data_dir"], config["signal_file"])

    try:
        signal_df = read_signal_file(signal_path)
        start_date = signal_df["日期"].min().strftime("%Y-%m-%d")
        end_date = signal_df["日期"].max().strftime("%Y-%m-%d")
        print(f"自动解析时间范围: {start_date} 到 {end_date}")
    except Exception as e:
        print(f"解析信号文件日期失败: {e}")
        raise

    # 3. 创建回测框架 - 使用自动解析的日期
    framework = BacktestFramework(
        signal_file=config["signal_file"],
        start_date=start_date,
        end_date=end_date,
        rank_n=config["rank_n"],
        rebalance_frequency=config["rebalance_frequency"],
        portfolio_count=config["portfolio_count"],
        data_dir=config["data_dir"],
        cache_dir=config["cache_dir"],
        output_dir=config["output_dir"],
    )

    # 4. 执行回测
    print(f"\n开始执行回测...")

    framework.run_backtest()
    print(f"\n回测完成！")
    print("=" * 60)


if __name__ == "__main__":

    load_config_and_run()
