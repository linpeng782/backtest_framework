import pandas as pd
import numpy as np
import os
import sys
import re
from pathlib import Path

from data_utils import *


def parse_stock_info_from_filename(filename):
    """
    从文件名解析股票信息
    输入: "000001.SZ-股票名称-日线后复权及常用指标-20250718.csv"
    输出: ("000001.SZ", "股票名称", "20250718")
    """
    pattern = r"([0-9]{6}\.[A-Z]{2})-(.+?)-日线后复权及常用指标-(\d{8})\.csv"
    match = re.match(pattern, filename)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None


def convert_stock_code(original_code):
    """
    转换股票代码格式
    SZ -> XSHE, SH -> XSHG, BJ -> BJSE
    """
    if original_code.endswith(".SZ"):
        return original_code.replace(".SZ", ".XSHE")
    elif original_code.endswith(".SH"):
        return original_code.replace(".SH", ".XSHG")
    elif original_code.endswith(".BJ"):
        return original_code.replace(".BJ", ".BJSE")
    else:
        return None  # 其他格式暂不处理


def get_stock_list_from_csv_folder(csv_folder_path, limit=None):
    """
    从CSV文件夹获取股票列表
    """
    csv_folder = Path(csv_folder_path)
    stock_list = []

    for csv_file in csv_folder.glob("*.csv"):
        original_code, stock_name, date = parse_stock_info_from_filename(csv_file.name)

        if original_code and stock_name:
            # 转换股票代码
            converted_code = convert_stock_code(original_code)

            if converted_code:  # 处理SZ、SH和BJ股票
                stock_list.append(
                    {
                        "original_code": original_code,
                        "converted_code": converted_code,
                        "stock_name": stock_name,
                        "date": date,
                    }
                )

    # # 限制处理数量（用于测试）
    # if limit:
    #     stock_list = stock_list[:limit]

    # 提取所有converted_code作为返回值
    converted_codes = [stock["converted_code"] for stock in stock_list]

    return converted_codes


def mask_producing(stock_list, stock_universe, cache_dir):

    date_list = stock_universe.index.tolist()

    st_filter = get_st_filter(stock_list, date_list)
    suspended_filter = get_suspended_filter(stock_list, date_list)
    limit_up_filter = get_limit_up_filter(stock_list, date_list)

    # # 检查哪些股票有null值
    # print("检查st_filter中的null值:")
    # st_null_stocks = st_filter.columns[st_filter.isnull().any()].tolist()
    # print(f"st_filter中有null值的股票: {st_null_stocks}")
    # print(f"总共{len(st_null_stocks)}只股票")

    # print("\n检查suspended_filter中的null值:")
    # suspended_null_stocks = suspended_filter.columns[
    #     suspended_filter.isnull().any()
    # ].tolist()
    # print(f"suspended_filter中有null值的股票: {suspended_null_stocks}")
    # print(f"总共{len(suspended_null_stocks)}只股票")

    # print("\n检查limit_up_filter中的null值:")
    # limit_up_null_stocks = limit_up_filter.columns[
    #     limit_up_filter.isnull().any()
    # ].tolist()
    # print(f"limit_up_filter中有null值的股票: {limit_up_null_stocks}")
    # print(f"总共{len(limit_up_null_stocks)}只股票")

    # 填充null值为False（表示不过滤）
    st_filter = st_filter.fillna(True)
    suspended_filter = suspended_filter.fillna(True)
    limit_up_filter = limit_up_filter.fillna(True)

    combo_mask = (
        st_filter.astype(int)
        + suspended_filter.astype(int)
        + limit_up_filter.astype(int)
    ) == 0

    combo_mask.to_csv(os.path.join(cache_dir, "combo_mask_tb.csv"))
    print("combo_mask saved to " + os.path.join(cache_dir, "combo_mask_tb.csv"))


def vwap_producing(stock_list, stock_universe, cache_dir):

    start_date = stock_universe.index.min()
    end_date = stock_universe.index.max()

    tech_list = ["total_turnover", "volume"]
    daily_tech = get_price(
        stock_list,
        start_date,
        end_date,
        fields=tech_list,
        adjust_type="post_volume",
        skip_suspended=False,
    ).sort_index()

    # 计算后复权VWAP（成交额/后复权调整后的成交量）
    post_vwap = daily_tech["total_turnover"] / daily_tech["volume"]

    # 获取未复权VWAP价格数据
    unadjusted_vwap = get_vwap(stock_list, start_date, end_date)

    # 转换为DataFrame并添加后复权VWAP
    vwap_df = pd.DataFrame({"unadjusted_vwap": unadjusted_vwap, "post_vwap": post_vwap})

    # 统一索引名称
    vwap_df.index.names = ["order_book_id", "datetime"]

    vwap_df.to_csv(os.path.join(cache_dir, "vwap_df_tb.csv"))
    print("vwap_df saved to " + os.path.join(cache_dir, "vwap_df_tb.csv"))


def trading_days_producing(stock_universe, cache_dir):

    start_date = stock_universe.index.min()
    end_date = stock_universe.index.max()
    trading_days = pd.DataFrame(get_trading_dates(start_date, end_date))
    trading_days.columns = ["datetime"]
    trading_days.to_csv(os.path.join(cache_dir, "trading_days.csv"))
    print("trading_days saved to " + os.path.join(cache_dir, "trading_days.csv"))


def benchmark_producing(stock_universe, cache_dir, benchmark_index="000985.XSHG"):

    start_date = stock_universe.index.min()
    end_date = stock_universe.index.max()
    benchmark = get_price(
        [benchmark_index],
        start_date,
        end_date,
        fields=["open"],
        adjust_type="none",
    ).open.unstack("order_book_id")
    benchmark.index.names = ["datetime"]
    benchmark.to_csv(os.path.join(cache_dir, "benchmark.csv"))
    print("benchmark saved to " + os.path.join(cache_dir, "benchmark.csv"))


if __name__ == "__main__":

    start_date = "2010-01-01"
    end_date = "2025-09-20"
    # 券池指数
    index_item = "000985.XSHG"
    # 缓存目录
    cache_dir = "/Users/didi/DATA/dnn_model/cache"

    # 基准指数
    benchmark_index = "000852.XSHG"
    # 股票池
    stock_universe = INDEX_FIX(start_date, end_date, index_item)

    # trading_days_producing(stock_universe, cache_dir)
    # benchmark_producing(stock_universe, cache_dir, benchmark_index)

    # 从淘宝购买的全A股票池目录
    csv_folder_path = "/Users/didi/DATA/dnn_model/raw/日线后复权及常用指标csv"
    # 获取从淘宝购买的全A股票池
    stock_list = get_stock_list_from_csv_folder(csv_folder_path)

    # vwap_producing(stock_list, stock_universe, cache_dir)
    mask_producing(stock_list, stock_universe, cache_dir)
