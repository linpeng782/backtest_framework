import pandas as pd
import numpy as np
import os
import sys

from data_utils import *


if __name__ == "__main__":

    start_date = "2010-01-01"
    end_date = "2025-09-20"
    index_item = "000985.XSHG"

    stock_universe = INDEX_FIX(start_date, end_date, index_item)
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

    # combo_mask.to_pickle("/Users/didi/DATA/dnn_model/cache/combo_mask.pkl")
    combo_mask.to_csv("/Users/didi/DATA/dnn_model/cache/combo_mask.csv")
    print("combo_mask saved to /Users/didi/DATA/dnn_model/cache/combo_mask.csv")
