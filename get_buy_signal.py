"""
信号处理模块
专门负责投资组合权重计算和信号处理逻辑
"""

import pandas as pd
import numpy as np
import os
import sys

sys.path.insert(0, "/Users/didi/dnn_model")
from factor_utils.factor_analysis import get_st_filter, get_suspended_filter

# 导入信号文件读取模块
from signal_reader import read_and_parse_signal_file


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


def apply_filters_and_select_stocks(pivot_df, rank_n):
    """
    应用过滤器并进行股票选择
    
    Args:
        pivot_df: 透视表格式的信号数据
        rank_n: 每日选股数量
        
    Returns:
        DataFrame: 经过过滤和选择的投资组合权重
    """
    date_list = pivot_df.index.tolist()
    stock_list = pivot_df.columns.tolist()

    # 1. 获取ST过滤和停牌过滤
    print("应用ST和停牌过滤...")
    st_filter = get_st_filter(stock_list, date_list)
    suspended_filter = get_suspended_filter(stock_list, date_list)
    suspended_filter.index.names = ["日期"]
    
    # 应用过滤器
    filtered_pivot = pivot_df.mask(suspended_filter).mask(st_filter)

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


def get_buy_signal(file_path, rank_n=30):
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
    portfolio_weights = apply_filters_and_select_stocks(pivot_df, rank_n)
    
    if portfolio_weights is None or portfolio_weights.empty:
        print("错误：无法生成投资组合权重")
        return None
    
    print(f"投资组合权重矩阵形状: {portfolio_weights.shape}")
    print(f"交易日期数量: {len(portfolio_weights.index)}")
    print(f"股票数量: {len(portfolio_weights.columns)}")
    
    return portfolio_weights


def get_signal_file_path(signal_filename, base_dir="/Users/didi/DATA/dnn_model/signal"):
    """
    获取信号文件的完整路径
    
    Args:
        signal_filename: 信号文件名
        base_dir: 信号文件基础目录
        
    Returns:
        str: 信号文件的完整路径
    """
    return os.path.join(base_dir, signal_filename)


def get_output_file_path(signal_filename, rank_n, output_dir=None):
    """
    生成输出文件的完整路径
    
    Args:
        signal_filename: 信号文件名，格式如 "20160104_20250819_signal"
        rank_n: 选股数量
        output_dir: 输出目录，默认使用统一目录
        
    Returns:
        str: 输出文件的完整路径，格式为 "startdate_enddate_rankn_weights.pkl"
    """
    import re
    
    # 默认输出目录
    if output_dir is None:
        output_dir = "/Users/didi/DATA/dnn_model/buy_list"
    
    # 确保目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 从信号文件名中提取日期信息
    base_name = os.path.splitext(signal_filename)[0]  # 去掉扩展名
    
    # 使用正则表达式提取日期
    date_pattern = r"(\d{8})_(\d{8})"
    match = re.search(date_pattern, base_name)
    
    if match:
        start_date = match.group(1)
        end_date = match.group(2)
        output_filename = f"{start_date}_{end_date}_rank{rank_n}_weights.pkl"
    else:
        # 如果无法提取日期，使用原始文件名
        print(f"警告：无法从文件名 '{signal_filename}' 中提取日期，使用原始格式")
        output_filename = f"{base_name}_rank{rank_n}_weights.pkl"
    
    output_file = os.path.join(output_dir, output_filename)
    return output_file


if __name__ == "__main__":
    # 测试信号处理功能
    signal_filename = "20200102_20250825_signal"  # 信号文件名
    rank_n = 30  # 选股数量
    
    # 获取信号文件路径
    signal_file = get_signal_file_path(signal_filename)
    
    # 检查文件是否存在
    if not os.path.exists(signal_file):
        print(f"错误：信号文件不存在: {signal_file}")
        signal_dir = os.path.dirname(signal_file)
        print(f"请确保文件存在于: {signal_dir}")
        exit(1)
    
    print("="*50)
    print("测试信号处理功能")
    print("="*50)
    print(f"信号文件: {signal_file}")
    print(f"选股数量: {rank_n}")
    
    # 生成投资组合权重
    portfolio_weights = get_buy_signal(signal_file, rank_n=rank_n)
    
    if portfolio_weights is not None:
        # 获取输出文件路径
        output_file = get_output_file_path(signal_filename, rank_n)
        print(f"输出文件: {os.path.basename(output_file)}")
        
        # 保存结果
        portfolio_weights.to_pickle(output_file)
        
        # 保存为CSV格式
        csv_file = output_file.replace('.pkl', '.csv')
        portfolio_weights.to_csv(csv_file)
        
        print(f"\\n结果保存:")
        print(f"  PKL文件: {output_file}")
        print(f"  CSV文件: {csv_file}")
        print(f"  数据形状: {portfolio_weights.shape}")
        
        # 显示统计信息
        print(f"\\n数据统计:")
        print(f"  交易日期数: {len(portfolio_weights.index)}")
        print(f"  股票数量: {len(portfolio_weights.columns)}")
        print(f"  非空权重数: {portfolio_weights.notna().sum().sum()}")
    else:
        print("生成投资组合权重失败！")
