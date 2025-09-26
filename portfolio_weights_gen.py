"""
信号处理模块
专门负责投资组合权重计算和信号处理逻辑
"""

import pandas as pd
import numpy as np
import os
import sys

from signal_reader import read_and_parse_signal_file
from data_utils import (
    get_st_filter,
    get_suspended_filter,
    get_limit_up_filter,
    get_new_stock_filter,
)


# 动态选股：确保每日选出rank_n只股票（考虑停牌过滤）
def select_top_n_stocks(row, n):
    """
    从每行中选出排名最前的n只股票（跳过NaN）

    Args:
        row: 包含股票排名的Series
        n: 要选择的股票数量

    Returns:
        Series: 选中的股票标记为1，其余为NaN
    """
    # 获取非空值的排名
    valid_scores = row.dropna()
    if len(valid_scores) == 0:
        return pd.Series(index=row.index, dtype=float)  # 全部返回NaN

    # 按排名升序排序，取前n个（排名越小越好）
    top_n_stocks = valid_scores.nsmallest(n).index

    # 创建结果序列
    result = pd.Series(index=row.index, dtype=float)
    result[top_n_stocks] = 1  # 被选中的股票设为1

    return result


def apply_filters_and_select_stocks(pivot_df, cache_dir, rank_n):
    """
    应用过滤器并进行股票选择

    Args:
        pivot_df: 透视表格式的信号数据
        rank_n: 每日选股数量
        cache_dir: 缓存目录

    Returns:
        DataFrame: 经过过滤和选择的投资组合权重
    """

    # 1. 获取ST过滤、停牌过滤和涨停过滤
    print("过滤：新股、ST、停牌、开盘涨停")

    # date_list = pivot_df.index.tolist()
    # stock_list = pivot_df.columns.tolist()
    # st_filter = get_st_filter(stock_list, date_list)
    # suspended_filter = get_suspended_filter(stock_list, date_list)
    # limit_up_filter = get_limit_up_filter(stock_list, date_list)
    # filtered_pivot = (
    #     pivot_df.mask(suspended_filter).mask(st_filter).mask(limit_up_filter)
    # )

    combo_mask = pd.read_csv(os.path.join(cache_dir, "combo_mask.csv"), index_col=[0])
    combo_mask.index = pd.to_datetime(combo_mask.index)
    filtered_pivot = pivot_df.mask(~combo_mask)

    # 2. 对每一行（每个交易日）应用选股逻辑
    print(f"开始动态选股，目标每日选出{rank_n}只股票...")
    filtered_pivot = filtered_pivot.apply(
        lambda row: select_top_n_stocks(row, rank_n), axis=1
    )

    # 3. 删除从未被选中的股票（列删除）
    filtered_pivot = filtered_pivot.dropna(axis=1, how="all")

    # 4. 向后推移一天（避免未来函数）
    buy_list = filtered_pivot.shift(1)

    # 5. 删除完全没有信号的日期（行删除）
    buy_list = buy_list.dropna(how="all")

    # 6. 计算权重
    portfolio_weights = buy_list.div(buy_list.sum(axis=1), axis=0)

    return portfolio_weights


def generate_portfolio_weights(file_path, cache_dir, rank_n=30):
    """
    从信号文件生成投资组合权重

    Args:
        file_path: 信号文件的完整路径
        rank_n: 每日选股数量

    Returns:
        DataFrame: 投资组合权重矩阵
    """
    print(f"处理信号文件: {file_path}")
    print(f"选股数量: {rank_n}")

    # 1. 读取信号文件并转换为透视表
    pivot_df = read_and_parse_signal_file(file_path)

    if pivot_df is None or pivot_df.empty:
        print("错误：无法读取或解析信号文件")
        return None

    print(f"信号数据形状: {pivot_df.shape}")
    print(f"时间范围: {pivot_df.index.min().date()} 到 {pivot_df.index.max().date()}")

    # 2. 应用过滤器并选择股票
    portfolio_weights = apply_filters_and_select_stocks(pivot_df, cache_dir, rank_n)

    if portfolio_weights is None or portfolio_weights.empty:
        print("错误：无法生成投资组合权重")
        return None

    print(f"投资组合权重矩阵形状: {portfolio_weights.shape}")
    print(f"交易日期数量: {len(portfolio_weights.index)}")
    print(f"股票数量: {len(portfolio_weights.columns)}")

    return portfolio_weights
