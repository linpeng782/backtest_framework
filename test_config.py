"""
测试简化版YAML配置文件读取功能
"""

import sys
import os
import yaml

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load_config(config_file='backtest_config.yaml'):
    """简单的配置文件读取函数"""
    config_path = os.path.join(os.path.dirname(__file__), config_file)
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_config_loading():
    """测试配置文件加载功能"""
    
    print("=" * 50)
    print("测试简化版YAML配置文件读取")
    print("=" * 50)
    
    try:
        # 加载配置
        config = load_config()
        print("✓ 配置文件加载成功")
        
        # 测试各个配置项
        print(f"\n基本配置:")
        print(f"  信号文件: {config['basic']['signal_file']}")
        print(f"  数据目录: {config['basic']['data_dir']}")
        print(f"  保存目录: {config['basic']['save_dir']}")
        
        print(f"\n策略配置:")
        print(f"  选股数量: {config['strategy']['rank_n']}")
        print(f"  调仓频率: {config['strategy']['rebalance_frequency']}")
        print(f"  基准指数: {config['strategy']['benchmark']}")
        print(f"  组合数量: {config['strategy']['portfolio_count']}")
        
        print(f"\n输出配置:")
        print(f"  保存结果: {config['output']['save_results']}")
        print(f"  输出目录: {config['output']['output_dir']}")
        
        print(f"\n显示配置:")
        print(f"  详细日志: {config['display']['verbose']}")
        print(f"  显示进度: {config['display']['show_progress']}")
        
        print(f"\n✅ 所有配置项读取成功！")
        
        # 显示完整配置结构
        print(f"\n完整配置结构:")
        for section, values in config.items():
            print(f"  {section}:")
            for key, value in values.items():
                print(f"    {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_config_loading()
    if success:
        print(f"\n🎉 配置文件测试通过！")
    else:
        print(f"\n💥 配置文件测试失败！")
