"""
OOP回测系统
基于原有回测代码重构的面向对象版本
保持原有功能不变，提供更简洁的使用接口
"""

from .complete_backtest import CompleteBacktestFramework
from .signal_reader import read_signal_file, get_stock_list_from_signal, detect_signal_format
from .get_buy_signal import get_buy_signal

__version__ = "1.0.0"
__all__ = ["CompleteBacktestFramework", "read_signal_file", "get_stock_list_from_signal", "detect_signal_format", "get_buy_signal"]
