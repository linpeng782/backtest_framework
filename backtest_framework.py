"""
完整的端到端量化回测框架
从原始信号文件到最终业绩分析的完整流程
"""

import pandas as pd
import numpy as np
import os
import sys
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime
from tqdm import tqdm


# 当作为脚本直接执行时的导入方式
from get_buy_signal import get_buy_signal
from backtest_rolling_flexible import rolling_backtest
from signal_reader import get_stock_list_from_signal
from performance_analyzer import get_performance_analysis

# 添加父目录到路径以导入回测模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入因子工具包
from factor_utils import get_price, get_vwap


class CompleteBacktestFramework:
    """
    完整的端到端量化回测框架

    包含完整的回测流程：
    1. 数据获取 (get_bar_data, get_vwap_data)
    2. 信号处理 (get_buy_signal)
    3. 回测执行 (backtest)
    4. 性能分析 (performance_analysis)

    每个步骤都有清晰的函数界面，便于理解和调试
    """

    def __init__(
        self,
        signal_file: str,
        start_date: str,
        end_date: str,
        rank_n: int = 30,
        rebalance_frequency: int = 5,
        portfolio_count: int = 5,
        initial_capital: float = 100000000,
        stamp_tax_rate: float = 0.0005,
        transfer_fee_rate: float = 0.0001,
        commission_rate: float = 0.0002,
        min_transaction_fee: float = 5,
        data_root: str = "/Users/didi/DATA/dnn_model",
        benchmark: str = "000852.XSHG",
    ):
        """
        初始化回测框架

        Args:
            signal_file: 信号文件名
            start_date: 开始日期
            end_date: 结束日期
            rank_n: 每日选股数量
            rebalance_frequency: 调仓频率（天）
            portfolio_count: 组合数量（资金分割份数）
            initial_capital: 初始资金
            stamp_tax_rate: 印花税率
            transfer_fee_rate: 过户费率
            commission_rate: 佣金率
            min_transaction_fee: 最低交易手续费
            data_root: 数据根目录
            benchmark: 基准指数
        """
        # 保存配置参数
        self.signal_file = signal_file
        self.start_date = start_date
        self.end_date = end_date
        self.rank_n = rank_n
        self.rebalance_frequency = rebalance_frequency
        self.portfolio_count = portfolio_count
        self.initial_capital = initial_capital
        self.stamp_tax_rate = stamp_tax_rate
        self.transfer_fee_rate = transfer_fee_rate
        self.commission_rate = commission_rate
        self.min_transaction_fee = min_transaction_fee
        self.data_root = data_root
        self.benchmark = benchmark

        print(f"初始化回测框架 - 信号文件: {signal_file}")
        print(f"回测时间范围: {start_date} 到 {end_date}")
        print(f"初始资金: {initial_capital:,.0f} 元")

    # ==================== 数据获取模块 ====================

    def get_vwap_data(self, stock_list: List[str]) -> pd.DataFrame:
        """
        步骤1.3: 获取VWAP数据（可选）

        Args:
            stock_list: 股票代码列表

        Returns:
            VWAP数据 DataFrame，包含 vwap 和 post_vwap 两列
        """
        print("\n=== 步骤1.3: 获取VWAP数据 ===")

        # 首先尝试从文件加载现有数据
        vwap_filename = f"{self.end_date.replace('-', '')}_vwap_df.csv"
        # 调整VWAP数据路径，data_root已经是具体目录，需要回到上级目录找bars
        parent_dir = os.path.dirname(self.data_root)
        vwap_path = os.path.join(parent_dir, "bars", vwap_filename)

        if os.path.exists(vwap_path):
            print(f"从文件加载VWAP数据: {vwap_path}")
            vwap_df = pd.read_csv(vwap_path)
            vwap_df["datetime"] = pd.to_datetime(vwap_df["datetime"])
            vwap_df = vwap_df.set_index(["order_book_id", "datetime"])
            print(f"VWAP数据形状: {vwap_df.shape}")
            return vwap_df
        else:
            print(f"VWAP数据文件不存在: {vwap_path}")
            print("开始实时获取VWAP数据...")

            try:
                # 使用与独立文件相同的逻辑获取VWAP数据
                print(f"获取VWAP数据，时间范围: {self.start_date} 到 {self.end_date}")
                print(f"股票数量: {len(stock_list)}")

                # 获取技术指标数据：成交额和成交量
                tech_list = ["total_turnover", "volume"]
                daily_tech = get_price(
                    stock_list,
                    self.start_date,
                    self.end_date,
                    fields=tech_list,
                    adjust_type="post_volume",
                    skip_suspended=False,
                ).sort_index()

                # 计算后复权VWAP（成交额/后复权调整后的成交量）
                post_vwap = daily_tech["total_turnover"] / daily_tech["volume"]

                # 获取未复权VWAP价格数据
                vwap_data = get_vwap(stock_list, self.start_date, self.end_date)

                # 转换为DataFrame并添加后复权VWAP
                vwap_df = pd.DataFrame({"vwap": vwap_data, "post_vwap": post_vwap})

                # 统一索引名称
                vwap_df.index.names = ["order_book_id", "datetime"]

                print(f"VWAP数据获取完成，形状: {vwap_df.shape}")

                # 保存数据以备下次使用
                print(f"保存VWAP数据到: {vwap_path}")
                os.makedirs(os.path.dirname(vwap_path), exist_ok=True)
                vwap_df.to_csv(vwap_path)

                return vwap_df

            except Exception as e:
                print(f"获取VWAP数据时出错: {e}")
                print("跳过VWAP数据获取，返回None")
                return None

    # ==================== 信号处理模块 ====================

    def generate_portfolio_weights(self) -> pd.DataFrame:
        """
        步骤2: 生成投资组合权重

        Returns:
            投资组合权重矩阵 DataFrame
        """
        print("\n=== 步骤2: 生成投资组合权重 ===")

        signal_path = os.path.join(self.data_root, self.signal_file)

        print(f"处理信号文件: {signal_path}")
        print(f"选股数量: {self.rank_n}")

        portfolio_weights = get_buy_signal(signal_path, rank_n=self.rank_n)

        if portfolio_weights is None:
            raise ValueError("生成投资组合权重失败")

        print(f"投资组合权重矩阵形状: {portfolio_weights.shape}")
        print(f"交易日期数量: {len(portfolio_weights.index)}")
        print(f"股票数量: {len(portfolio_weights.columns)}")

        return portfolio_weights

    def save_results(self, results: Dict[str, Any]) -> None:
        """
        步骤5: 保存回测结果（可选）

        Args:
            results: 回测结果字典
        """
        print("\n=== 步骤5: 保存回测结果 ===")

        # 创建输出目录
        parent_dir = os.path.dirname(self.data_root)
        output_dir = os.path.join(parent_dir, "backtest_results")
        os.makedirs(output_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_filename = f"backtest_result_{self.signal_file}_{timestamp}"

        # 保存账户历史记录
        account_result = results["account_result"]
        account_csv_path = os.path.join(output_dir, f"{result_filename}_account.csv")
        account_result.to_csv(account_csv_path)
        print(f"账户历史记录已保存: {account_csv_path}")

        # 保存性能指标
        performance_metrics = results["performance_metrics"]
        metrics_csv_path = os.path.join(output_dir, f"{result_filename}_metrics.csv")
        pd.DataFrame([performance_metrics]).to_csv(metrics_csv_path, index=False)
        print(f"性能指标已保存: {metrics_csv_path}")

        # 保存投资组合权重
        portfolio_weights = results["portfolio_weights"]
        weights_csv_path = os.path.join(output_dir, f"{result_filename}_weights.csv")
        portfolio_weights.to_csv(weights_csv_path)
        print(f"投资组合权重已保存: {weights_csv_path}")

    # ==================== 主执行流程 ====================

    def run_backtest(self) -> Dict[str, Any]:
        """
        执行完整的回测流程

        Returns:
            包含所有结果的字典
        """
        print("\n" + "=" * 60)
        print("开始完整的端到端回测流程")
        print("=" * 60)

        try:
            # 步骤1: 数据获取
            signal_path = os.path.join(self.data_root, self.signal_file)
            stock_list = get_stock_list_from_signal(signal_path)
            
            # 获取VWAP数据
            vwap_df = self.get_vwap_data(stock_list)

            # 步骤2: 信号处理
            portfolio_weights = self.generate_portfolio_weights()

            account_result = rolling_backtest(
                portfolio_weights=portfolio_weights,
                bars_df=vwap_df,
                portfolio_count=self.portfolio_count,
                rebalance_frequency=self.rebalance_frequency,
            )

            # 步骤3: 回测执行
            # account_result = self.run_backtest_engine(portfolio_weights, vwap_df)

            # 步骤4: 性能分析 - 直接使用独立的性能分析模块
            print("\n=== 步骤4: 分析回测性能 ===")
            print("使用独立的性能分析模块计算性能指标...")

            # 调用独立的性能分析函数
            performance_cumnet, result = get_performance_analysis(
                account_result=account_result, benchmark_index=self.benchmark
            )

            # 转换结果格式以保持一致性
            performance_metrics = {
                "总收益率": result["策略累计收益"],
                "年化收益率": result["策略年化收益"],
                "年化波动率": result["波动率"],
                "夏普比率": result["夏普比率"],
                "最大回撤": result["最大回撤"],
                "胜率": result["日胜率"],
                "交易天数": len(account_result) - 1,
                "最终资产": account_result["total_account_asset"].iloc[-1],
                # 添加完整的性能指标
                "基准累计收益": result["基准累计收益"],
                "基准年化收益": result["基准年化收益"],
                "阿尔法": result["阿尔法"],
                "贝塔": result["贝塔"],
                "超额累计收益": result["超额累计收益"],
                "超额年化收益": result["超额年化收益"],
                "信息比率": result["信息比率"],
                "索提诺比率": result["索提诺比率"],
            }

            print("\n性能指标汇总:")
            for key, value in performance_metrics.items():
                if key in [
                    "总收益率",
                    "年化收益率",
                    "年化波动率",
                    "最大回撤",
                    "胜率",
                    "基准累计收益",
                    "基准年化收益",
                    "超额累计收益",
                    "超额年化收益",
                ]:
                    print(f"  {key}: {value:.2%}")
                elif key in ["夏普比率", "阿尔法", "贝塔", "信息比率", "索提诺比率"]:
                    print(f"  {key}: {value:.3f}")
                elif key == "最终资产":
                    print(f"  {key}: {value:,.0f} 元")
                else:
                    print(f"  {key}: {value}")

            print("\n" + "=" * 60)
            print("回测流程完成！")
            print("=" * 60)

            # 返回所有结果
            results = {
                "stock_list": stock_list,
                "portfolio_weights": portfolio_weights,
                "account_result": account_result,
                "performance_metrics": performance_metrics,
                "performance_cumnet": performance_cumnet,
                "vwap_df": vwap_df,
            }

            # 可选：保存结果
            # self.save_results(results)

            return results

        except Exception as e:
            print(f"\n回测过程中发生错误: {str(e)}")
            raise
