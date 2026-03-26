import pandas as pd
import numpy as np
import os
import time

start_time = time.time()
def filter_outliers(df, threshold, window=5):
    """
    剔除偏离局部均值的异常点（包括单点和连续段）。
    参数：
        df: DataFrame，第一列为时间，其余为数据列
        threshold: 滤波阈值
        window: 滑动窗口半径（前后各取 window 个有效点计算均值）
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
        
        # 构建一个字典，将原始索引映射到其在有效数组中的位置（便于快速找前后 window 个点）
        # 由于 valid_idx 是递增的，我们可以直接使用二分查找
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
            mean_val = np.mean(window_vals)
            
            if abs(val - mean_val) > threshold:
                remove_mask[idx] = True
        
        # 将被标记的点设为 NaN
        df_filtered.loc[remove_mask, col] = np.nan
    return df_filtered

def process_excel(file_path, thresholds=None, default_threshold=None, window=5, output_suffix='_filtered'):
    """
    处理Excel文件，支持为每个工作表设置不同的滤波阈值。
    参数：
        file_path: 输入Excel文件路径
        thresholds: 字典，工作表名 -> 阈值
        default_threshold: 默认阈值（未在 thresholds 中指定的工作表使用）
        window: 滑动窗口半径（默认5，即前后各5个点）
        output_suffix: 输出文件名后缀
    """
    if not os.path.exists(file_path):
        print(f"错误：文件 {file_path} 不存在")
        return
    
    sheets = pd.read_excel(file_path, sheet_name=None, dtype=object)
    processed_sheets = {}
    
    for sheet_name, df in sheets.items():
        # 确定该工作表的阈值
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
        
        print(f"正在处理工作表：{sheet_name} (阈值={thresh}, 窗口半径={window})")
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
    # 设置不同工作表的阈值（示例）
    thresholds = {
        'Side_Temperature':0.5,
        'Side_Strain':2,
        'Middle_Temperature':0.5,
        'Middle_Strain':2,
        'Top_Temperature':0.5,
        'Top_Strain':2,
    }
    input_file = "E:\\Documents\\BYD电池测试\\数据文件\\20260315_low_C_Rate\\数据汇总.xlsx"
    # 窗口半径可根据数据密集程度调整，建议5-10
    process_excel(input_file, thresholds=thresholds, default_threshold=10.0, window=100)

end_time = time.time()
run_time = end_time - start_time
print(f"\n代码运行时间：{run_time:.4f} 秒")