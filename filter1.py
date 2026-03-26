import pandas as pd
import numpy as np
import os
import time

start_time = time.time()

def filter_outliers(df, threshold, window=5):
    """
    剔除偏离局部中位数的异常点（基于 MAD 自适应阈值）。
    参数：
        df: DataFrame，第一列为时间，其余为数据列
        threshold: MAD 的倍数（如 3 表示 |x - median| > 3 * MAD 的点被剔除）
        window: 滑动窗口半径（前后各取 window 个有效点计算中位数和 MAD）
    """
    df_filtered = df.copy()
    for col in df.columns[1:]:
        # 转换为数值，非数值转为 NaN
        numeric_series = pd.to_numeric(df[col], errors='coerce')
        df_filtered[col] = numeric_series
        data = numeric_series.values
        
        # 获取有效值的索引和值
        valid_idx = np.where(~pd.isna(data))[0]
        n_valid = len(valid_idx)
        if n_valid < 2 * window + 1:
            # 有效点数不足，无法形成有效窗口，跳过该列
            continue
        
        # 初始化移除掩码
        remove_mask = np.zeros(len(data), dtype=bool)
        
        for i in range(n_valid):
            idx = valid_idx[i]   # 原始索引
            val = data[idx]
            
            # 确定窗口范围：前 window 个有效点、后 window 个有效点
            start = max(0, i - window)
            end = min(n_valid, i + window + 1)
            # 窗口内的有效索引（不包括当前点本身）
            window_indices = [valid_idx[j] for j in range(start, end) if j != i]
            if len(window_indices) < 2 * window:
                # 窗口内点数不足，跳过该点（保留）
                continue
            
            window_vals = data[window_indices]
            # 计算窗口内中位数
            median_val = np.median(window_vals)
            # 计算绝对中位差 MAD = median(|x_i - median|)
            abs_dev = np.abs(window_vals - median_val)
            mad = np.median(abs_dev)
            
            # 判定异常：如果 MAD == 0，则任何偏离中位数的点都视为异常
            if mad == 0:
                if val != median_val:
                    remove_mask[idx] = True
            else:
                if abs(val - median_val) > threshold * mad:
                    remove_mask[idx] = True
        
        # 将被标记的点设为 NaN
        df_filtered.loc[remove_mask, col] = np.nan
    return df_filtered

def process_excel(file_path, thresholds=None, default_threshold=None, window=5, output_suffix='_filtered'):
    """
    处理Excel文件，支持为每个工作表设置不同的滤波阈值（此处阈值表示 MAD 倍数）。
    参数：
        file_path: 输入Excel文件路径
        thresholds: 字典，工作表名 -> MAD 倍数
        default_threshold: 默认 MAD 倍数（未在 thresholds 中指定的工作表使用）
        window: 滑动窗口半径（默认5，即前后各5个点）
        output_suffix: 输出文件名后缀
    """
    if not os.path.exists(file_path):
        print(f"错误：文件 {file_path} 不存在")
        return
    
    sheets = pd.read_excel(file_path, sheet_name=None, dtype=object)
    processed_sheets = {}
    
    for sheet_name, df in sheets.items():
        # 确定该工作表的 MAD 倍数
        if thresholds is not None and sheet_name in thresholds:
            thresh = thresholds[sheet_name]
        else:
            thresh = default_threshold
        
        if thresh is None:
            print(f"工作表 '{sheet_name}' 未指定阈值，跳过滤波处理")
            processed_sheets[sheet_name] = df
            continue
        
        if df.shape[1] < 2:
            print(f"工作表 '{sheet_name}' 只有一列，跳过滤波")
            processed_sheets[sheet_name] = df
            continue
        
        print(f"正在处理工作表：{sheet_name} (MAD倍数={thresh}, 窗口半径={window})")
        filtered_df = filter_outliers(df, thresh, window)
        processed_sheets[sheet_name] = filtered_df
    
    # 保存结果
    dir_name = os.path.dirname(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    ext = os.path.splitext(file_path)[1] or '.xlsx'
    output_path = os.path.join(dir_name, f"{base_name}{output_suffix}{ext}")
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for sheet_name, df in processed_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"处理完成，结果已保存至：{output_path}")

if __name__ == "__main__":
    # 设置不同工作表的 MAD 倍数（示例：温度类用3倍MAD，应变类用2.5倍MAD）
    thresholds = {
        'Side_Temperature': 3.0,
        'Side_Strain': 2.5,
        'Middle_Temperature': 3.0,
        'Middle_Strain': 2.5,
        'Top_Temperature': 3.0,
        'Top_Strain': 2.5,
    }
    input_file = "E:\\Documents\\BYD电池测试\\数据文件\\20260315_low_C_Rate\\数据汇总.xlsx"
    # 窗口半径可根据数据密集程度调整，建议5-10；默认阈值用于未列出的工作表
    process_excel(input_file, thresholds=thresholds, default_threshold=3.0, window=10)

end_time = time.time()
run_time = end_time - start_time
print(f"\n代码运行时间：{run_time:.4f} 秒")