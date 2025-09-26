#!/usr/bin/env python3
"""
数据覆盖检查模块
检查缓存数据是否能够完全覆盖信号文件的需求
确保回测数据的完整性和一致性
"""

import pandas as pd
import os
from typing import Dict, Set
from signal_reader import read_signal_file


def check_vwap_coverage(
    signal_stocks: Set, signal_dates: Set, cache_dir: str, vwap_filename: str
):
    """检查VWAP数据覆盖情况，如果有缺失直接报错"""

    vwap_path = os.path.join(cache_dir, vwap_filename)

    if not os.path.exists(vwap_path):
        raise FileNotFoundError(f"VWAP文件不存在: {vwap_path}")

    # 读取VWAP数据
    vwap_df = pd.read_csv(vwap_path)
    vwap_df["datetime"] = pd.to_datetime(vwap_df["datetime"])

    vwap_stocks = set(vwap_df["order_book_id"].unique())
    vwap_dates = set(vwap_df["datetime"].dt.date)

    missing_stocks = signal_stocks - vwap_stocks
    missing_dates = signal_dates - vwap_dates

    if missing_stocks:
        raise ValueError(
            f"VWAP数据缺失股票 ({len(missing_stocks)}个): {sorted(list(missing_stocks))[:10]}..."
        )

    if missing_dates:
        raise ValueError(
            f"VWAP数据缺失日期 ({len(missing_dates)}个): {sorted(list(missing_dates))[:10]}..."
        )

    print(f"✅ VWAP数据覆盖检查通过")


def check_mask_coverage(
    signal_stocks: Set, signal_dates: Set, cache_dir: str, mask_filename: str
):
    """检查Mask数据覆盖情况，如果有缺失直接报错"""

    mask_path = os.path.join(cache_dir, mask_filename)

    if not os.path.exists(mask_path):
        raise FileNotFoundError(f"Mask文件不存在: {mask_path}")

    # 读取Mask数据
    mask_df = pd.read_csv(mask_path, index_col=[0])
    mask_df.index = pd.to_datetime(mask_df.index)

    mask_stocks = set(mask_df.columns)
    mask_dates = set(mask_df.index.date)

    missing_stocks = signal_stocks - mask_stocks
    missing_dates = signal_dates - mask_dates

    if missing_stocks:
        raise ValueError(
            f"Mask数据缺失股票 ({len(missing_stocks)}个): {sorted(list(missing_stocks))[:10]}..."
        )

    if missing_dates:
        raise ValueError(
            f"Mask数据缺失日期 ({len(missing_dates)}个): {sorted(list(missing_dates))[:10]}..."
        )

    print(f"✅ Mask数据覆盖检查通过")


def check_data_coverage_for_signal(
    signal_path: str,
    cache_dir: str,
    vwap_filename: str = "vwap_df_tb.csv",
    mask_filename: str = "combo_mask_tb.csv",
):
    """
    检查指定信号文件的数据覆盖情况，如果有缺失直接报错停止程序

    Args:
        signal_path: 信号文件路径
        cache_dir: 缓存目录路径
        vwap_filename: VWAP文件名
    """
    print("=" * 80)
    print("开始数据覆盖检查")
    print("=" * 80)

    # 1. 读取信号文件
    print(f"\n📊 读取信号文件: {signal_path}")
    signal_df = read_signal_file(signal_path)

    signal_stocks = set(signal_df["股票代码"].unique())
    signal_dates = set(pd.to_datetime(signal_df["日期"]).dt.date)
    signal_start = signal_df["日期"].min()
    signal_end = signal_df["日期"].max()

    print(f"   信号文件统计:")
    print(f"   - 股票数量: {len(signal_stocks)}")
    print(f"   - 日期范围: {signal_start.date()} 到 {signal_end.date()}")
    print(f"   - 总记录数: {len(signal_df)}")

    # 2. 检查VWAP数据覆盖（如果有缺失会直接抛出异常）
    print(f"\n📈 检查VWAP数据覆盖...")
    check_vwap_coverage(signal_stocks, signal_dates, cache_dir, vwap_filename)

    # 3. 检查Mask数据覆盖（如果有缺失会直接抛出异常）
    print(f"\n🎭 检查Mask数据覆盖...")
    check_mask_coverage(signal_stocks, signal_dates, cache_dir, mask_filename)

    print("=" * 80)
