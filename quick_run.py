#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速运行示例：展示温度密度模型和风场模型的基本用法
"""

import sys
import os

# 确保可以导入model模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # 导入我们的模型接口
    from model import (
        TempDensityModel, 
        WindModel,
        convert_date_to_day,
        calculate_seconds_of_day
    )
    print("成功导入模型接口模块")
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

def run_temp_density_example():
    """
    温度密度模型示例
    """
    print("\n=== 温度密度模型示例 ===")
    
    try:
        # 创建模型实例
        model = TempDensityModel()
        print("温度密度模型初始化成功")
        
        # 准备输入参数（2023年1月1日，12:00:00 UTC）
        year, month, day = 2023, 1, 1
        hour, minute, second = 12, 0, 0
        
        # 转换日期和时间
        day_of_year = convert_date_to_day(year, month, day)
        seconds_of_day = calculate_seconds_of_day(hour, minute, second)
        
        print(f"日期: {year}-{month}-{day} -> 年内日数: {day_of_year}")
        print(f"时间: {hour}:{minute}:{second} -> 当天秒数: {seconds_of_day}")
        
        # 单点计算示例
        result = model.calculate_point(
            day=day_of_year,
            utsec=seconds_of_day,
            alt_km=100.0,       # 100公里高度
            lat_deg=35.0,       # 北纬35度
            lon_deg=116.0,      # 东经116度
            f107a=100.0,        # F10.7指数
            f107=100.0,         # F10.7指数
            ap7=None            # 使用默认地磁指数
        )
        
        # 打印结果
        print(f"\n单点计算结果（100km高度）:")
        print(f"  局部温度: {result.T_local_K:.2f} K")
        print(f"  外温度: {result.T_exo_K:.2f} K")
        print(f"  N2密度: {result.densities[0]:.2e} cm^-3")
        print(f"  O2密度: {result.densities[1]:.2e} cm^-3")
        print(f"  O密度: {result.densities[2]:.2e} cm^-3")
        
        # 批量计算示例（不同高度）
        print("\n批量计算示例（不同高度）:")
        altitudes = [80.0, 100.0, 120.0, 150.0]
        
        # 使用相同的其他参数，只改变高度
        batch_results = model.calculate_batch(
            day=day_of_year,
            utsec=seconds_of_day,
            alt_km=altitudes,
            lat_deg=35.0,
            lon_deg=116.0,
            f107a=100.0,
            f107=100.0,
            output_as_dict=False
        )
        
        # 打印批量结果
        print("高度(km) | 局部温度(K) | N2密度(cm^-3) | O密度(cm^-3)")
        print("---------|------------|--------------|-------------")
        for i, res in enumerate(batch_results):
            print(f"{res.alt_km:9.1f} | {res.T_local_K:10.2f} | {res.densities[0]:12.2e} | {res.densities[2]:11.2e}")
            
    except Exception as e:
        print(f"温度密度模型运行失败: {e}")

def run_wind_example():
    """
    风场模型示例
    """
    print("\n=== 风场模型示例 ===")
    
    try:
        # 创建模型实例
        model = WindModel()
        print("风场模型初始化成功")
        
        # 准备输入参数（2023年1月1日，格式为YYYYDDD）
        iyd = 2023001  # 2023年第1天
        sec = 43200.0  # 12:00:00 UTC
        
        print(f"日期: 2023-01-01 (IYD: {iyd})")
        print(f"时间: 12:00:00 UTC (秒: {sec})")
        
        # 单点计算示例
        meridional_wind, zonal_wind = model.calculate_point(
            iyd=iyd,
            sec=sec,
            alt_km=100.0,       # 100公里高度
            glat_deg=35.0,      # 北纬35度
            glon_deg=116.0,     # 东经116度
            stl_hours=12.0,     # 本地太阳时
            f107a=100.0,        # F10.7指数
            f107=100.0,         # F10.7指数
            ap2=(0.0, 20.0)     # 地磁指数
        )
        
        # 打印结果
        print(f"\n单点计算结果（100km高度）:")
        print(f"  经向风（南北向）: {meridional_wind:.2f} m/s")
        print(f"  纬向风（东西向）: {zonal_wind:.2f} m/s")
        
        # 批量计算示例（不同高度）
        print("\n批量计算示例（不同高度）:")
        altitudes = [80.0, 100.0, 120.0, 150.0]
        
        # 使用相同的其他参数，只改变高度
        meridional_winds, zonal_winds = model.calculate_batch(
            iyd=iyd,
            sec=sec,
            alt_km=altitudes,
            glat_deg=35.0,
            glon_deg=116.0,
            stl_hours=12.0,
            f107a=100.0,
            f107=100.0,
            ap2=(0.0, 20.0)
        )
        
        # 打印批量结果
        print("高度(km) | 经向风(m/s) | 纬向风(m/s)")
        print("---------|------------|------------")
        for i, alt in enumerate(altitudes):
            print(f"{alt:9.1f} | {meridional_winds[i]:10.2f} | {zonal_winds[i]:10.2f}")
            
    except Exception as e:
        print(f"风场模型运行失败: {e}")

def main():
    """
    主函数：运行所有示例
    """
    print("UpperAtmPy 模型快速运行示例")
    print("==========================")
    
    # 运行温度密度模型示例
    run_temp_density_example()
    
    # 运行风场模型示例
    run_wind_example()
    
    print("\n示例运行完成！")

if __name__ == "__main__":
    main()