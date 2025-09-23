"""
简化版回测执行脚本
读取配置文件并执行回测，简单直接
"""

import sys
import os
import yaml
from datetime import datetime

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
        print(f"✓ 配置文件加载成功")
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        raise

    # 2. 从信号文件中自动解析日期范围
    print(f"\n正在从信号文件解析日期范围...")
    signal_path = os.path.join(config["data_dir"], config["signal_file"])

    try:
        signal_df = read_signal_file(signal_path)
        start_date = signal_df["日期"].min().strftime("%Y-%m-%d")
        end_date = signal_df["日期"].max().strftime("%Y-%m-%d")
        print(f"✓ 自动解析时间范围: {start_date} 到 {end_date}")
    except Exception as e:
        print(f"❌ 解析信号文件日期失败: {e}")
        raise

    # 3. 创建回测框架 - 使用自动解析的日期
    framework = BacktestFramework(
        signal_file=config["signal_file"],
        start_date=start_date,
        end_date=end_date,
        rank_n=config["rank_n"],
        rebalance_frequency=config["rebalance_frequency"],
        portfolio_count=config["portfolio_count"],
        data_root=config["data_dir"],
        benchmark=config["benchmark"],
    )

    # 4. 执行回测
    print(f"\n开始执行回测...")
    framework.run_backtest()

    # 6. 保存结果（如果配置了保存）
    if config["save_results"]:
        save_results(results, config)

    print(f"\n回测完成！")
    print("=" * 60)

    return results


def save_results(results, config):
    """保存回测结果到文件"""

    print(f"\n正在保存回测结果...")

    # 创建输出目录
    output_dir = os.path.join(config["save_dir"], config["output_dir"])
    os.makedirs(output_dir, exist_ok=True)

    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    signal_name = config["signal_file"].replace("/", "_")
    result_filename = f"backtest_{signal_name}_{timestamp}"

    try:
        # 保存账户历史记录
        account_result = results["account_result"]
        account_csv_path = os.path.join(output_dir, f"{result_filename}_account.csv")
        account_result.to_csv(account_csv_path)
        print(f"  账户历史: {account_csv_path}")

        # 保存性能指标
        performance_metrics = results["performance_metrics"]
        import pandas as pd

        metrics_csv_path = os.path.join(output_dir, f"{result_filename}_metrics.csv")
        pd.DataFrame([performance_metrics]).to_csv(metrics_csv_path, index=False)
        print(f"  性能指标: {metrics_csv_path}")

        # 保存投资组合权重
        if "portfolio_weights" in results:
            portfolio_weights = results["portfolio_weights"]
            weights_csv_path = os.path.join(
                output_dir, f"{result_filename}_weights.csv"
            )
            portfolio_weights.to_csv(weights_csv_path)
            print(f"  投资组合权重: {weights_csv_path}")

        print(f"  结果保存完成！")

    except Exception as e:
        print(f"  保存结果时出错: {e}")


def main():
    """主函数"""
    try:
        results = load_config_and_run()
        return results
    except FileNotFoundError as e:
        print(f"\n❌ 文件未找到: {e}")
        print(f"请检查配置文件中的路径设置是否正确")
    except Exception as e:
        print(f"\n❌ 执行过程中出现错误: {e}")


if __name__ == "__main__":

    results = main()
