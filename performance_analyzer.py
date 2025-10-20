"""
性能分析模块

该模块提供统一的回测性能分析功能，支持：
- 收益率计算（总收益率、年化收益率等）
- 风险指标计算（夏普比率、最大回撤、波动率等）
- 基准比较分析（阿尔法、贝塔、信息比率等）
- 可视化图表生成

职责分离原则：
- 专注于性能分析计算逻辑
- 与回测引擎解耦
- 可被多个回测框架复用
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
import statsmodels.api as sm
import os
from datetime import datetime
from typing import Dict, Any, Tuple, Optional
from data_utils import *
from rolling_backtest import get_previous_trading_date_from_df


def get_benchmark(
    account_result: pd.DataFrame,
    trading_days_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
) -> pd.Series:
    """
    获取基准指数数据

    Args:
        account_result: 账户历史记录
        benchmark_df: 基准指数数据

    Returns:
        基准指数价格序列
    """

    # 获取开始日期前一个交易日
    start_date = get_previous_trading_date_from_df(
        trading_days_df, account_result.index.min(), 1
    ).strftime("%Y-%m-%d")
    end_date = account_result.index.max().strftime("%Y-%m-%d")

    # 市场指数基准
    price_open = benchmark_df.loc[start_date:end_date]

    return price_open


def get_performance_analysis(
    account_result: pd.DataFrame,
    trading_days_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    portfolio_count: int,
    rank_n: int,
    save_path: str,
    annual_turnover: float,
    rf: float = 0.03,
    show_plot: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    综合性能分析函数

    Args:
        account_result: 账户历史记录，包含 total_account_asset 列
        rf: 无风险利率，默认 3%
        benchmark_df: 基准指数数据
        save_path: 图表保存路径（可选）
        show_plot: 是否显示图表
        portfolio_count: 组合数量（资金分割份数）
        rank_n: 每日选股数量
    Returns:
        Tuple[pd.DataFrame, Dict]: (累计收益率数据, 性能指标字典)
    """

    # 加入基准数据
    performance = pd.concat(
        [
            account_result["total_account_asset"].to_frame("strategy"),
            get_benchmark(account_result, trading_days_df, benchmark_df),
        ],
        axis=1,
    )

    performance_net = performance.pct_change().dropna(how="all")  # 日收益率
    performance_cumnet = (1 + performance_net).cumprod()  # 累计收益
    performance_cumnet["alpha"] = (
        performance_cumnet["strategy"] / performance_cumnet[benchmark_df.columns[0]]
    )
    performance_cumnet = performance_cumnet.fillna(1)

    # 指标计算
    performance_pct = performance_cumnet.pct_change().dropna()

    # 策略收益
    strategy_name, benchmark_name, alpha_name = performance_cumnet.columns.tolist()
    Strategy_Final_Return = performance_cumnet[strategy_name].iloc[-1] - 1

    # 策略年化收益
    Strategy_Annualized_Return_EAR = (1 + Strategy_Final_Return) ** (
        252 / len(performance_cumnet)
    ) - 1

    # 基准收益
    Benchmark_Final_Return = performance_cumnet[benchmark_name].iloc[-1] - 1

    # 基准年化收益
    Benchmark_Annualized_Return_EAR = (1 + Benchmark_Final_Return) ** (
        252 / len(performance_cumnet)
    ) - 1

    # Alpha 和 Beta 计算
    try:
        # 清理数据，移除异常值
        strategy_excess_returns = performance_pct[strategy_name] * 252 - rf
        benchmark_excess_returns = performance_pct[benchmark_name] * 252 - rf

        # 移除NaN和无穷大值
        valid_mask = (
            pd.notnull(strategy_excess_returns)
            & pd.notnull(benchmark_excess_returns)
            & np.isfinite(strategy_excess_returns)
            & np.isfinite(benchmark_excess_returns)
        )

        strategy_clean = strategy_excess_returns[valid_mask]
        benchmark_clean = benchmark_excess_returns[valid_mask]

        if len(strategy_clean) > 5:  # 确保有足够的数据点
            ols_result = sm.OLS(
                strategy_clean,
                sm.add_constant(benchmark_clean),
            ).fit()
            Alpha = ols_result.params[0]
            Beta = ols_result.params[1]
        else:
            print("警告：数据点不足，使用默认Alpha和Beta值")
            Alpha = 0.0
            Beta = 1.0

    except Exception as e:
        print(f"线性回归失败: {e}，使用默认Alpha和Beta值")
        Alpha = 0.0
        Beta = 1.0

    # 波动率
    Strategy_Volatility = performance_pct[strategy_name].std() * np.sqrt(252)

    # 夏普比率
    Strategy_Sharpe = (Strategy_Annualized_Return_EAR - rf) / Strategy_Volatility

    # 下行波动率
    strategy_ret = performance_pct[strategy_name]
    Strategy_Down_Volatility = strategy_ret[strategy_ret < 0].std() * np.sqrt(252)

    # 索提诺比率
    Sortino = (Strategy_Annualized_Return_EAR - rf) / Strategy_Down_Volatility

    # 跟踪误差
    Tracking_Error = (
        performance_pct[strategy_name] - performance_pct[benchmark_name]
    ).std() * np.sqrt(252)

    # 信息比率
    Information_Ratio = (
        Strategy_Annualized_Return_EAR - Benchmark_Annualized_Return_EAR
    ) / Tracking_Error

    # 最大回撤
    i = np.argmax(
        (
            np.maximum.accumulate(performance_cumnet[strategy_name])
            - performance_cumnet[strategy_name]
        )
        / np.maximum.accumulate(performance_cumnet[strategy_name])
    )
    j = np.argmax(performance_cumnet[strategy_name][:i])
    Max_Drawdown = (
        1 - performance_cumnet[strategy_name][i] / performance_cumnet[strategy_name][j]
    )

    # 卡玛比率
    Calmar = (Strategy_Annualized_Return_EAR) / Max_Drawdown

    # 超额收益
    Alpha_Final_Return = performance_cumnet[alpha_name].iloc[-1] - 1

    # 超额年化收益
    Alpha_Annualized_Return_EAR = (1 + Alpha_Final_Return) ** (
        252 / len(performance_cumnet)
    ) - 1

    # 超额波动率
    Alpha_Volatility = performance_pct[alpha_name].std() * np.sqrt(252)

    # 超额夏普比率
    Alpha_Sharpe = (Alpha_Annualized_Return_EAR - rf) / Alpha_Volatility

    # 超额最大回撤
    i = np.argmax(
        (
            np.maximum.accumulate(performance_cumnet[alpha_name])
            - performance_cumnet[alpha_name]
        )
        / np.maximum.accumulate(performance_cumnet[alpha_name])
    )
    j = np.argmax(performance_cumnet[alpha_name][:i])
    Alpha_Max_Drawdown = (
        1 - performance_cumnet[alpha_name][i] / performance_cumnet[alpha_name][j]
    )

    # 胜率
    performance_pct["win"] = performance_pct[alpha_name] > 0
    Win_Ratio = performance_pct["win"].value_counts().loc[True] / len(performance_pct)

    # 盈亏比
    profit_lose = performance_pct.groupby("win")[alpha_name].mean()
    Profit_Lose_Ratio = abs(profit_lose[True] / profit_lose[False])

    # 汇总结果
    result = {
        "策略累计收益": round(Strategy_Final_Return, 4),
        "策略年化收益": round(Strategy_Annualized_Return_EAR, 4),
        "基准累计收益": round(Benchmark_Final_Return, 4),
        "基准年化收益": round(Benchmark_Annualized_Return_EAR, 4),
        "阿尔法": round(Alpha, 4),
        "贝塔": round(Beta, 4),
        "波动率": round(Strategy_Volatility, 4),
        "夏普比率": round(Strategy_Sharpe, 4),
        "下行波动率": round(Strategy_Down_Volatility, 4),
        "索提诺比率": round(Sortino, 4),
        "跟踪误差": round(Tracking_Error, 4),
        "信息比率": round(Information_Ratio, 4),
        "最大回撤": round(Max_Drawdown, 4),
        "卡玛比率": round(Calmar, 4),
        "超额累计收益": round(Alpha_Final_Return, 4),
        "超额年化收益": round(Alpha_Annualized_Return_EAR, 4),
        "超额波动率": round(Alpha_Volatility, 4),
        "超额夏普": round(Alpha_Sharpe, 4),
        "超额最大回撤": round(Alpha_Max_Drawdown, 4),
        "日胜率": round(Win_Ratio, 4),
        "盈亏比": round(Profit_Lose_Ratio, 4),
        "换手率": round(annual_turnover, 4),
    }

    # 年度收益分析
    performance_annual_performance = (
        performance_cumnet.pct_change()
        .resample("Y")
        .apply(lambda x: (1 + x).prod() - 1)
        .T
    )

    # 生成图表（如果需要）
    if save_path:
        _generate_performance_charts(
            performance_cumnet,
            result,
            portfolio_count,
            rank_n,
            benchmark_df.columns[0],
            save_path,
            show_plot,
        )

    # 打印结果表格到控制台
    print(pd.DataFrame([result]).T)
    print(performance_annual_performance.T)


def _generate_performance_charts(
    performance_cumnet: pd.DataFrame,
    result: Dict[str, Any],
    portfolio_count: Optional[int],
    rank_n: Optional[int],
    benchmark_index: str,
    save_path: Optional[str],
    show_plot: bool,
) -> None:
    """
    生成性能分析图表
    """
    # 设置中文字体
    rcParams["font.sans-serif"] = ["SimHei", "Arial Unicode MS", "DejaVu Sans"]
    rcParams["axes.unicode_minus"] = False

    # 生成文件名和路径
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    start_date = performance_cumnet.index[0].strftime("%Y-%m-%d")
    end_date = performance_cumnet.index[-1].strftime("%Y-%m-%d")

    # 直接在save_dir下生成文件
    chart_filename = f"rolling_{portfolio_count}_{rank_n}_{benchmark_index}_{start_date}_{end_date}_{timestamp}_chart.png"
    table_filename = f"rolling_{portfolio_count}_{rank_n}_{benchmark_index}_{start_date}_{end_date}_{timestamp}_table.png"
    chart_path = os.path.join(save_path, chart_filename)
    table_path = os.path.join(save_path, table_filename)

    strategy_name, benchmark_name, alpha_name = performance_cumnet.columns.tolist()

    # ==================== 图1：收益曲线图 ====================
    fig1, ax1 = plt.subplots(figsize=(16, 9))

    # 绘制策略和基准收益曲线
    ax1.plot(
        performance_cumnet.index,
        performance_cumnet[strategy_name],
        color="#1f77b4",
        linewidth=2.5,
        label="策略收益",
        alpha=0.9,
    )
    ax1.plot(
        performance_cumnet.index,
        performance_cumnet[benchmark_name],
        color="#ff7f0e",
        linewidth=2.5,
        label="基准收益",
        alpha=0.9,
    )

    # 创建第二个y轴显示超额收益
    ax2 = ax1.twinx()
    ax2.plot(
        performance_cumnet.index,
        performance_cumnet[alpha_name],
        color="#2ca02c",
        linewidth=2,
        alpha=0.7,
        label="超额收益",
    )
    ax2.set_ylabel("超额收益", color="#2ca02c", fontsize=12)
    ax2.tick_params(axis="y", labelcolor="#2ca02c")

    # 设置主图样式
    title = f"rolling_{portfolio_count}_{rank_n}_{start_date}_{end_date}_{timestamp}_收益曲线分析"
    ax1.set_title(title, fontsize=18, fontweight="bold", pad=20)
    ax1.set_xlabel("日期", fontsize=12)
    ax1.set_ylabel("累积收益", fontsize=12)
    ax1.grid(True, alpha=0.3, linestyle="--")
    ax1.legend(loc="upper left", fontsize=11)
    ax2.legend(loc="upper right", fontsize=11)

    # 美化图表
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax2.spines["top"].set_visible(False)

    plt.tight_layout()

    # 保存收益曲线图
    if chart_path:
        plt.savefig(chart_path, dpi=300, bbox_inches="tight", facecolor="white")
        print(f"收益曲线图已保存到: {chart_path}")

    if show_plot:
        plt.show()
    else:
        plt.close()

    # ==================== 图2：绩效指标表 ====================
    fig2, ax3 = plt.subplots(figsize=(12, 16))
    ax3.axis("off")

    # 准备表格数据
    result_df = pd.DataFrame([result]).T
    result_df.columns = ["数值"]

    # 创建表格数据
    table_data = []
    for idx, row in result_df.iterrows():
        table_data.append([idx, f"{row['数值']:.4f}"])

    # 绘制表格
    table = ax3.table(
        cellText=table_data,
        colLabels=["绩效指标", "数值"],
        cellLoc="left",
        loc="center",
        colWidths=[0.7, 0.3],
    )

    # 设置表格样式
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 2.2)

    # 设置表头样式
    for i in range(2):
        table[(0, i)].set_facecolor("#4472C4")
        table[(0, i)].set_text_props(weight="bold", color="white", size=14)

    # 设置交替行颜色和样式
    for i in range(1, len(table_data) + 1):
        if i % 2 == 0:
            for j in range(2):
                table[(i, j)].set_facecolor("#F8F9FA")
        table[(i, 1)].set_text_props(weight="bold")

    # 添加标题
    title = f"rolling_{portfolio_count}_{rank_n}_{start_date}_{end_date}_{timestamp}_绩效指标表"
    ax3.text(
        0.5,
        0.95,
        title,
        transform=ax3.transAxes,
        fontsize=18,
        fontweight="bold",
        ha="center",
        va="top",
    )

    plt.tight_layout()

    # 保存绩效指标表
    if table_path:
        plt.savefig(table_path, dpi=300, bbox_inches="tight", facecolor="white")
        print(f"绩效指标表已保存到: {table_path}")

    if show_plot:
        plt.show()
    else:
        plt.close()
