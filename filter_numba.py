import pandas as pd
import numpy as np
from numba import jit
import os
import time

start_time = time.time()

@jit(nopython=True)
def _filter_column_numba(data, window, threshold):
    """
    Numba 加速的单列滤波核心
    参数：
        data: numpy 数组（一维），包含原始数据（含 NaN）
        window: 窗口半径
        threshold: MAD 倍数
    返回：
        mask: bool 数组，True 表示该位置应被剔除
    """
    n = len(data)
    mask = np.zeros(n, dtype=np.bool_)
    # 获取有效值索引
    valid_idx = []
    for i in range(n):
        if not np.isnan(data[i]):
            valid_idx.append(i)
    n_valid = len(valid_idx)
    if n_valid < 2 * window + 1:
        return mask

    # 预先将 valid_idx 转为 numpy 数组以加快索引
    valid_idx_arr = np.array(valid_idx, dtype=np.int64)
    # 遍历每个有效点
    for pos in range(n_valid):
        idx = valid_idx_arr[pos]
        val = data[idx]

        # 窗口边界（在有效点列表中的索引）
        start = max(0, pos - window)
        end = min(n_valid, pos + window + 1)

        # 收集窗口内其他有效点的值
        window_vals = []
        for j in range(start, end):
            if j == pos:
                continue
            window_vals.append(data[valid_idx_arr[j]])
        if len(window_vals) < 2 * window:
            continue

        # 计算中位数和 MAD
        window_vals_arr = np.array(window_vals)
        median = np.median(window_vals_arr)
        abs_dev = np.abs(window_vals_arr - median)
        mad = np.median(abs_dev)

        if mad == 0:
            if val != median:
                mask[idx] = True
        else:
            if abs(val - median) > threshold * mad:
                mask[idx] = True
    return mask

def filter_outliers(df, threshold, window=5):
    """
    对 DataFrame 各列应用 Numba 加速的滤波
    """
    df_filtered = df.copy()
    for col in df.columns[1:]:
        numeric_series = pd.to_numeric(df[col], errors='coerce')
        data = numeric_series.values.astype(np.float64)
        mask = _filter_column_numba(data, window, threshold)
        df_filtered.loc[mask, col] = np.nan
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
    
    sheets = pd.read_excel(file_path, sheet_name=None, dtype=object, engine='calamine')
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
    
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        for sheet_name, df in processed_sheets.items():
           df.to_excel(writer, sheet_name=sheet_name, index=False)
    '''
    # 保存为多个 CSV 文件，每个工作表一个文件
    for sheet_name, df in processed_sheets.items():
    # 构建输出文件名：原文件名 + 后缀 + '_' + 工作表名 + .csv
        csv_filename = f"{base_name}{output_suffix}_{sheet_name}.csv"
        csv_path = os.path.join(dir_name, csv_filename)
        df.to_csv(csv_path, index=False)
        print(f"已保存工作表 '{sheet_name}' 至：{csv_path}")

    '''
    
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
    input_file = r"E:\Documents\BYD电池测试\数据文件\20260317_50_cycle\1_33_cycle\数据汇总.xlsx"
    # 窗口半径可根据数据密集程度调整，建议5-10；默认阈值用于未列出的工作表
    process_excel(input_file, thresholds=thresholds, default_threshold=3.0, window=10)

end_time = time.time()
run_time = end_time - start_time
print(f"\n代码运行时间：{run_time:.4f} 秒")





