"""
完整的端到端量化回测框架
从原始信号文件到最终业绩分析的完整流程
"""

import pandas as pd
import numpy as np
import os
import sys
from typing import Dict, Any, Tuple, Optional, List
from data_utils import *
from performance_analyzer import get_performance_analysis
from portfolio_weights_gen import generate_portfolio_weights
from rolling_backtest import rolling_backtest
from signal_reader import get_stock_list_from_signal
from data_coverage_checker import check_data_coverage_for_signal
from loguru import logger


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
        output_dir: str = None,  # 保存输出的目录
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
            cache_dir: 保存数据的目录
            output_dir: 保存输出的目录
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
        self.output_dir = output_dir

        logger.info(f"初始化回测框架 - 信号文件: {signal_file}")
        logger.info(f"回测时间范围: {start_date} 到 {end_date}")

    # ==================== 数据获取模块 ====================

    def get_vwap_data(self) -> pd.DataFrame:

        # filename = "vwap_df.csv"
        filename = "vwap_df_tb.csv"
        vwap_df = pd.read_csv(os.path.join(self.cache_dir, filename))
        vwap_df["datetime"] = pd.to_datetime(vwap_df["datetime"])
        vwap_df = vwap_df.set_index(["order_book_id", "datetime"])
        return vwap_df

    def get_trading_days(self) -> pd.DataFrame:
        filename = "trading_days.csv"
        trading_days = pd.read_csv(
            os.path.join(self.cache_dir, filename), index_col=[0]
        )
        return trading_days

    def get_benchmark(self) -> pd.DataFrame:
        filename = "benchmark.csv"
        benchmark = pd.read_csv(os.path.join(self.cache_dir, filename))
        benchmark["datetime"] = pd.to_datetime(benchmark["datetime"])
        benchmark = benchmark.set_index(["datetime"])
        return benchmark

    # ==================== 主执行流程 ====================

    def run_backtest(self) -> Dict[str, Any]:
        """
        执行完整的回测流程

        Returns:
            包含所有结果的字典
        """
        logger.info("\n" + "=" * 60)
        logger.info("开始完整的端到端回测流程")
        logger.info("=" * 60)

        try:
            # 步骤1：数据覆盖检查
            logger.info("\n=== 步骤1: 数据覆盖检查 ===")
            signal_path = os.path.join(self.data_dir, self.signal_file)

            # 检查数据覆盖情况（如果有缺失会直接抛出异常停止程序）
            check_data_coverage_for_signal(signal_path, self.cache_dir)

            # 步骤2：获取vwap数据、交易日数据
            logger.info("\n=== 步骤2: 从缓存读取vwap、交易日历、指数基准数据 ===")
            vwap_df = self.get_vwap_data()
            trading_days = self.get_trading_days()
            benchmark = self.get_benchmark()

            # 交易日历数据已准备完成
            logger.info(f"交易日历数据加载完成，包含 {len(trading_days)} 个交易日")

            # 步骤3：生成投资组合权重
            logger.info("\n=== 步骤3: 生成投资组合权重 ===")
            portfolio_weights = generate_portfolio_weights(
                signal_path, rank_n=self.rank_n, cache_dir=self.cache_dir
            )

            # 步骤4：执行滚动回测
            logger.info("\n=== 步骤4: 执行滚动回测 ===")
            account_result = rolling_backtest(
                portfolio_weights=portfolio_weights,
                bars_df=vwap_df,
                trading_days_df=trading_days,
                portfolio_count=self.portfolio_count,
                rebalance_frequency=self.rebalance_frequency,
            )

            # 步骤5：策略回测结果
            logger.info("\n=== 步骤5: 策略回测结果 ===")
            get_performance_analysis(
                account_result=account_result,
                trading_days_df=trading_days,
                benchmark_df=benchmark,
                portfolio_count=self.portfolio_count,
                rank_n=self.rank_n,
                save_path=self.output_dir,
            )

        except Exception as e:
            logger.error(f"\n回测过程中发生错误: {str(e)}")
            raise
