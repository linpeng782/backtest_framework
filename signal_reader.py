"""
信号文件读取模块
专门负责读取和解析各种格式的信号文件
"""

import pandas as pd
import numpy as np
import os
import re
import sys


def add_exchange_suffix(stock_code):
    """
    根据股票代码添加相应的交易所后缀

    规则（根据米筐数据格式）：
    - 上交所：主板 (60)，科创板 (68) -> .XSHG
    - 深交所：主板 (00)，创业板 (30) -> .XSHE
    - 北交所：(43, 83, 87, 92) -> .BJSE
    """
    # 上交所：主板和科创板
    if stock_code.startswith(("60", "68")):
        return f"{stock_code}.XSHG"
    # 深交所：主板、创业板
    elif stock_code.startswith(("00", "30")):
        return f"{stock_code}.XSHE"
    # 北交所：所有类型
    elif stock_code.startswith(("43", "83", "87", "92")):
        return f"{stock_code}.BJSE"
    else:
        # 如果不匹配任何规则，保持原样并打印警告
        print(f"警告：股票代码 {stock_code} 不匹配任何交易所规则")
        return stock_code


def _parse_signal_with_rank(file_handle):
    """
    解析带排名的信号文件格式：日期 股票代码 排名
    """
    data = []
    for line in file_handle:
        line = line.strip()
        if line:  # 跳过空行
            parts = line.split()
            if len(parts) >= 3:
                date = parts[0]
                stock_code = parts[1]
                rank = int(parts[2])
                data.append({"日期": date, "股票代码": stock_code, "排名": rank})
    return data


def _parse_signal_without_rank(file_handle):
    """
    解析不带排名的信号文件格式：日期_股票代码
    根据每日出现顺序自动分配排名
    """
    data = []
    daily_rank = {}  # 记录每日的排名计数器

    for line in file_handle:
        line = line.strip()
        if line:  # 跳过空行
            if "_" in line and len(line.split("_")) == 2:
                date_str, stock_code = line.split("_")

                # 为每个日期维护独立的排名计数器
                if date_str not in daily_rank:
                    daily_rank[date_str] = -1

                daily_rank[date_str] += 1
                rank = daily_rank[date_str]

                data.append({"日期": date_str, "股票代码": stock_code, "排名": rank})
    return data


def detect_signal_format(file_path):
    """
    检测信号文件的格式

    Args:
        file_path: 信号文件路径

    Returns:
        str: 'with_rank' 或 'without_rank'
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            if "_" in first_line and len(first_line.split("_")) == 2:
                return "without_rank"  # 新格式：日期_股票代码
            else:
                return "with_rank"  # 旧格式：日期 股票代码 排名
    except Exception as e:
        print(f"检测文件格式时出错: {e}")
        return None


def read_signal_file(file_path):
    """
    读取信号文件并返回结构化数据

    Args:
        file_path: 信号文件的完整路径

    Returns:
        pandas.DataFrame: 包含日期、股票代码和排名的DataFrame
    """
    print(f"读取信号文件: {file_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"信号文件不存在: {file_path}")

    # 检测文件格式
    format_type = detect_signal_format(file_path)
    if format_type is None:
        return None

    print(f"检测到信号格式: {format_type}")

    # 读取文件数据
    data = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            if format_type == "without_rank":
                # 新格式：日期_股票代码（不带排名）
                data = _parse_signal_without_rank(f)
            else:
                # 旧格式：日期 股票代码 排名（带排名）
                data = _parse_signal_with_rank(f)

    except Exception as e:
        print(f"读取文件时出错: {e}")
        return None

    # 转换为DataFrame
    df = pd.DataFrame(data)

    if df.empty:
        print("警告：文件为空或没有有效数据")
        return df

    print(f"读取到 {len(df)} 条信号记录")

    try:
        # 尝试新格式：2020-01-02
        df["日期"] = pd.to_datetime(df["日期"], format="%Y-%m-%d")
    except ValueError:
        try:
            # 尝试旧格式：20160104
            df["日期"] = pd.to_datetime(df["日期"], format="%Y%m%d")
        except ValueError:
            print("使用自动推断格式")
            df["日期"] = pd.to_datetime(df["日期"])

    # 添加交易所后缀到股票代码
    df["股票代码"] = df["股票代码"].apply(add_exchange_suffix)

    return df


def convert_to_pivot_table(signal_df):
    """
    将信号数据转换为透视表格式

    Args:
        signal_df: 信号DataFrame，包含日期、股票代码、排名列

    Returns:
        pandas.DataFrame: 日期为行索引，股票代码为列标签，排名为值的透视表
    """
    if signal_df is None or signal_df.empty:
        return pd.DataFrame()

    print("转换数据为透视表格式...")

    # 将数据重构为透视表格式
    # 日期作为行索引，股票代码作为列标签，排名作为值
    pivot_df = signal_df.pivot_table(
        index="日期",
        columns="股票代码",
        values="排名",
        aggfunc="first",  # 如果有重复，取第一个值
    )

    return pivot_df


def get_stock_list_from_signal(file_path):
    """
    从信号文件中提取唯一股票列表

    Args:
        file_path: 信号文件路径

    Returns:
        list: 股票代码列表（带交易所后缀）
    """
    signal_df = read_signal_file(file_path)
    if signal_df is None or signal_df.empty:
        return []

    # 统计信息
    date_range = f"{signal_df['日期'].min().date()} 到 {signal_df['日期'].max().date()}"
    unique_stocks = signal_df["股票代码"].nunique()
    unique_dates = signal_df["日期"].nunique()

    print(f"数据统计:")
    print(f"  时间范围: {date_range}")
    print(f"  唯一股票数: {unique_stocks}")
    print(f"  交易日数: {unique_dates}")

    stock_list = sorted(signal_df["股票代码"].unique().tolist())

    return stock_list


# 向后兼容的函数
def read_and_parse_signal_file(file_path):
    """
    读取并解析信号文件，返回透视表格式的数据

    Args:
        file_path: 信号文件路径

    Returns:
        pandas.DataFrame: 透视表格式的信号数据
    """
    signal_df = read_signal_file(file_path)
    return convert_to_pivot_table(signal_df)
