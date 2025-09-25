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
from portfolio_weights_gen import generate_portfolio_weights
from rolling_backtest import rolling_backtest
from signal_reader import get_stock_list_from_signal
from performance_analyzer import get_performance_analysis
from data_utils import get_price, get_vwap


class BacktestFramework:
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
        data_dir: str = None,  # 数据目录
        cache_dir: str = None,  # 保存数据的目录
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
            data_dir: 数据目录
            save_dir: 保存数据的目录
            benchmark: 基准指数
        """
        # 保存配置参数
        self.signal_file = signal_file
        self.start_date = start_date
        self.end_date = end_date
        self.rank_n = rank_n
        self.rebalance_frequency = rebalance_frequency
        self.portfolio_count = portfolio_count
        self.data_dir = data_dir
        self.cache_dir = cache_dir
        self.benchmark = benchmark

        print(f"初始化回测框架 - 信号文件: {signal_file}")
        print(f"回测时间范围: {start_date} 到 {end_date}")

    # ==================== 数据获取模块 ====================

    def get_vwap_data(self, stock_list: List[str]) -> pd.DataFrame:
        """
        获取VWAP数据

        Args:
            stock_list: 股票代码列表

        Returns:
            VWAP数据 DataFrame，包含 vwap 和 post_vwap 两列
        """

        # 首先尝试从文件加载现有数据
        vwap_filename = f"{self.end_date.replace('-', '')}_vwap_df.csv"
        # 使用配置文件中的cache_dir作为VWAP数据保存路径
        vwap_path = os.path.join(self.cache_dir, vwap_filename)

        if os.path.exists(vwap_path):
            print(f"从文件加载VWAP数据: {vwap_path}")
            vwap_df = pd.read_csv(vwap_path)
            vwap_df["datetime"] = pd.to_datetime(vwap_df["datetime"])
            vwap_df = vwap_df.set_index(["order_book_id", "datetime"])
            return vwap_df
        else:
            print(f"VWAP数据文件不存在: {vwap_path}")
            print("开始实时获取VWAP数据...")

            try:
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
                unadjusted_vwap = get_vwap(stock_list, self.start_date, self.end_date)

                # 转换为DataFrame并添加后复权VWAP
                vwap_df = pd.DataFrame(
                    {"unadjusted_vwap": unadjusted_vwap, "post_vwap": post_vwap}
                )

                # 统一索引名称
                vwap_df.index.names = ["order_book_id", "datetime"]

                # 保存数据以备下次使用
                print(f"保存VWAP数据到: {vwap_path}")
                os.makedirs(os.path.dirname(vwap_path), exist_ok=True)
                vwap_df.to_csv(vwap_path)

                return vwap_df

            except Exception as e:
                print(f"获取VWAP数据时出错: {e}")
                print("跳过VWAP数据获取，返回None")
                return None

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
            # 步骤1: 获取vwap数据
            print("\n=== 步骤1: 获取vwap数据 ===")
            signal_path = os.path.join(self.data_dir, self.signal_file)

            stock_list = get_stock_list_from_signal(signal_path)
            vwap_df = self.get_vwap_data(stock_list)

            # 步骤2: 生成投资组合权重
            print("\n=== 步骤2: 生成投资组合权重 ===")
            portfolio_weights = generate_portfolio_weights(
                signal_path, rank_n=self.rank_n, cache_dir=self.cache_dir
            )

            # 步骤3: 执行滚动回测
            print("\n=== 步骤3: 执行滚动回测 ===")
            account_result = rolling_backtest(
                portfolio_weights=portfolio_weights,
                bars_df=vwap_df,
                portfolio_count=self.portfolio_count,
                rebalance_frequency=self.rebalance_frequency,
            )

            # 步骤4: 策略回测结果
            print("\n=== 步骤4: 策略回测结果 ===")
            get_performance_analysis(
                account_result=account_result,
                benchmark_index=self.benchmark,
                portfolio_count=self.portfolio_count,
                rank_n=self.rank_n,
            )

        except Exception as e:
            print(f"\n回测过程中发生错误: {str(e)}")
            raise
