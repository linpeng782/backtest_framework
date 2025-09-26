import pandas as pd
import numpy as np
import os
import sys

from data_utils import *


def mask_producing(stock_universe, cache_dir):

    stock_list = stock_universe.columns.tolist()
    date_list = stock_universe.index.tolist()

    st_filter = get_st_filter(stock_list, date_list)
    suspended_filter = get_suspended_filter(stock_list, date_list)
    limit_up_filter = get_limit_up_filter(stock_list, date_list)

    combo_mask = (
        st_filter.astype(int)
        + suspended_filter.astype(int)
        + limit_up_filter.astype(int)
    ) == 0

    combo_mask.to_csv(os.path.join(cache_dir, "combo_mask.csv"))
    print("combo_mask saved to " + os.path.join(cache_dir, "combo_mask.csv"))


def vwap_producing(stock_universe, cache_dir):

    stock_list = stock_universe.columns.tolist()
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

    vwap_df.to_csv(os.path.join(cache_dir, "vwap_df.csv"))
    print("vwap_df saved to " + os.path.join(cache_dir, "vwap_df.csv"))


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

    stock_universe = INDEX_FIX(start_date, end_date, index_item)

    # mask_producing(stock_universe, cache_dir)
    # vwap_producing(stock_universe, cache_dir)
    # trading_days_producing(stock_universe, cache_dir)
    benchmark_producing(stock_universe, cache_dir, benchmark_index)
