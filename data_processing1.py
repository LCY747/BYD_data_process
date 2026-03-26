import glob
import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 计时开始
start_time = time.time()

# =============================================================================
# 1. 数据导入：使用 pandas 读取所有 txt 文件并合并
# =============================================================================
file_path = r'E:\Documents\BYD电池测试\数据文件\20260311_SCT_0cycle\cycle3'
txt_files = glob.glob(os.path.join(file_path, "*.txt"))

df_list = []
for f in txt_files:
    # 假设文件用制表符分隔，编码为 gbk
    df = pd.read_csv(f, sep='\t', encoding='gbk')
    df_list.append(df)

# 合并所有数据，忽略索引
merged_df = pd.concat(df_list, ignore_index=True)

# 原始数据的列标题（第一行）
column_titles = merged_df.columns.tolist()

# =============================================================================
# 2. 提取光纤传感器对应的列索引
# =============================================================================
def get_column_indices(col_titles, ch_keyword, n_sensors=9):
    """
    根据通道关键词提取波长列的索引。
    假设数据中每个通道的波长与功率成对出现，波长列在前（每两列一组）。
    因此取匹配通道的前 n_sensors * 2 列中的波长列（即偶数索引）。
    """
    # 找出包含通道关键词的所有列
    matched_cols = [col for col in col_titles if ch_keyword in col]
    # 按原始顺序排序
    matched_cols.sort()
    # 取前 n_sensors * 2 列（即 9 对，18 列），如果不足则取全部
    matched_cols = matched_cols[:n_sensors * 2]
    # 波长列是这些列中的偶数索引（0,2,4,...）
    indices = [col_titles.index(col) for col in matched_cols][::2]
    return indices

# 获取各通道波长列的索引
index_FOS1 = get_column_indices(column_titles, '通道2')   # 侧边温度
index_FOS2 = get_column_indices(column_titles, '通道5')   # 侧边应变
index_FOS3 = get_column_indices(column_titles, '通道1')   # 大面中温度
index_FOS4 = get_column_indices(column_titles, '通道6')   # 大面中应变
index_FOS5 = get_column_indices(column_titles, '通道0')   # 大面上温度
index_FOS6 = get_column_indices(column_titles, '通道3')   # 大面上应变

# 检查是否都找到了 9 个传感器
assert len(index_FOS1) == len(index_FOS2) == len(index_FOS3) == len(index_FOS4) == len(index_FOS5) == len(index_FOS6) == 9, "传感器数量不正确，请检查列名"

# =============================================================================
# 3. 波长解耦为温度和应变（向量化计算）
# =============================================================================
T0 = 27.5          # 初始温度（℃）
k = 10             # 温度灵敏度系数（pm/℃）

# 初始波长（25℃下的波长，单位 nm）
WL0_temper_broadside = np.array([1529.9293, 1531.853, 1533.8734, 1535.8419,
                                 1537.7964, 1539.7262, 1541.739, 1543.7665, 1545.6947])
WL0_strain_broadside = np.array([1529.9792, 1532.0752, 1534.1012, 1536.0223,
                                 1538.0215, 1540.0045, 1541.9491, 1543.9012, 1545.8201])
WL0_temper_middle = np.array([1529.8577, 1531.8346, 1533.8264, 1535.7863, 1537.7731,
                              1539.6825, 1541.7218, 1543.6433, 1545.5896])
WL0_strain_middle = np.array([1530.0032, 1531.9487, 1533.8112, 1535.837,
                              1537.7677, 1539.8282, 1541.8026, 1543.8116, 1545.7057])
WL0_temper_top = np.array([1529.9009, 1531.8538, 1533.901, 1535.8004, 1537.8138,
                           1539.7491, 1541.73, 1543.6338, 1545.6028])
WL0_strain_top = np.array([1529.8198, 1531.7773, 1533.6188, 1535.5896, 1537.4503,
                           1539.5037, 1541.4901, 1543.4701, 1545.5015])

# 提取原始数据中的波长值（转换为浮点数）
temp_b_data = merged_df.iloc[:, index_FOS1].values.astype(float)
strain_b_data = merged_df.iloc[:, index_FOS2].values.astype(float)
temp_m_data = merged_df.iloc[:, index_FOS3].values.astype(float)
strain_m_data = merged_df.iloc[:, index_FOS4].values.astype(float)
temp_t_data = merged_df.iloc[:, index_FOS5].values.astype(float)
strain_t_data = merged_df.iloc[:, index_FOS6].values.astype(float)

# 向量化计算温度（℃）和应变（με）
temper_b = T0 + (temp_b_data - WL0_temper_broadside) * 1000 / k
strain_b = ((strain_b_data - WL0_strain_broadside) - (temp_b_data - WL0_temper_broadside)) * 1000

temper_m = T0 + (temp_m_data - WL0_temper_middle) * 1000 / k
strain_m = ((strain_m_data - WL0_strain_middle) - (temp_m_data - WL0_temper_middle)) * 1000

temper_t = T0 + (temp_t_data - WL0_temper_top) * 1000 / k
strain_t = ((strain_t_data - WL0_strain_top) - (temp_t_data - WL0_temper_top)) * 1000

# =============================================================================
# 4. 处理时间列，转换为 datetime 类型，作为索引
# =============================================================================
# 假设时间列是第一列（列名为 '时间' 或类似），实际可能为 'Time' 或 '时间'
time_col_name = column_titles[0]          # 第一列为时间
time_series = merged_df[time_col_name]

# 转换为 pandas datetime 格式（自动处理格式）
try:
    time_dt = pd.to_datetime(time_series, format="%Y/%m/%d/%H:%M:%S.%f")
except:
    # 如果上述格式不匹配，尝试常见格式
    time_dt = pd.to_datetime(time_series)

# 将时间设为索引，方便后续操作
temper_b_df = pd.DataFrame(temper_b, index=time_dt, columns=[f'FBG{i+1}' for i in range(9)])
strain_b_df = pd.DataFrame(strain_b, index=time_dt, columns=[f'FBG{i+1}' for i in range(9)])
temper_m_df = pd.DataFrame(temper_m, index=time_dt, columns=[f'FBG{i+1}' for i in range(9)])
strain_m_df = pd.DataFrame(strain_m, index=time_dt, columns=[f'FBG{i+1}' for i in range(9)])
temper_t_df = pd.DataFrame(temper_t, index=time_dt, columns=[f'FBG{i+1}' for i in range(9)])
strain_t_df = pd.DataFrame(strain_t, index=time_dt, columns=[f'FBG{i+1}' for i in range(9)])

# =============================================================================
# 5. 异常值处理：将绝对值超过 10000 的值设为 NaN，然后按时间线性插值
# =============================================================================
def clean_and_interpolate(df):
    df_clean = df.copy()
    # 异常值置 NaN
    df_clean[df_clean.abs() > 10000] = np.nan
    # 按时间线性插值（使用时间索引）
    df_clean = df_clean.interpolate(method='time')
    # 如果首尾仍有 NaN，向前/向后填充（可选）
    df_clean = df_clean.fillna(method='ffill').fillna(method='bfill')
    return df_clean

temper_b_df = clean_and_interpolate(temper_b_df)
strain_b_df = clean_and_interpolate(strain_b_df)
temper_m_df = clean_and_interpolate(temper_m_df)
strain_m_df = clean_and_interpolate(strain_m_df)
temper_t_df = clean_and_interpolate(temper_t_df)
strain_t_df = clean_and_interpolate(strain_t_df)

# =============================================================================
# 6. 降采样到 1Hz（取每秒第一个有效值）
# =============================================================================
# resample('1S') 按秒聚合，first() 取每秒第一个非 NaN 值
temper_b_1Hz = temper_b_df.resample('1s').first()
strain_b_1Hz = strain_b_df.resample('1s').first()
temper_m_1Hz = temper_m_df.resample('1s').first()
strain_m_1Hz = strain_m_df.resample('1s').first()
temper_t_1Hz = temper_t_df.resample('1s').first()
strain_t_1Hz = strain_t_df.resample('1s').first()

# =============================================================================
# 7. 根据起止时间提取目标片段
# =============================================================================
startTime = 20260312164632
endTime = 20260313004823

start_dt = pd.to_datetime(str(startTime), format='%Y%m%d%H%M%S')
end_dt = pd.to_datetime(str(endTime), format='%Y%m%d%H%M%S')

mask = (temper_b_1Hz.index >= start_dt) & (temper_b_1Hz.index <= end_dt)
temper_b_op = temper_b_1Hz[mask]
strain_b_op = strain_b_1Hz[mask]
temper_m_op = temper_m_1Hz[mask]
strain_m_op = strain_m_1Hz[mask]
temper_t_op = temper_t_1Hz[mask]
strain_t_op = strain_t_1Hz[mask]

# =============================================================================
# 8. 温度归一化与应变相对变化
# =============================================================================
# 温度归一化：每个 FBG 减去初始值，再加上第一个 FBG 的初始温度
initial_temp = temper_b_op.iloc[0, 0]          # 第一个 FBG 的第一个值
temper_b_cali = initial_temp + (temper_b_op - temper_b_op.iloc[0])
temper_m_cali = initial_temp + (temper_m_op - temper_m_op.iloc[0])
temper_t_cali = initial_temp + (temper_t_op - temper_t_op.iloc[0])

# 应变相对变化：减去初始应变
strain_b_cali = strain_b_op - strain_b_op.iloc[0]
strain_m_cali = strain_m_op - strain_m_op.iloc[0]
strain_t_cali = strain_t_op - strain_t_op.iloc[0]

# =============================================================================
# 9. 导出 Excel 文件
# =============================================================================
output_path = os.path.join(file_path, "数据汇总.xlsx")
with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    # 时间列（字符串格式，精确到秒）
    time_series_out = temper_b_op.index.strftime('%Y/%m/%d/%H:%M:%S')
    time_df = pd.DataFrame({'Time': time_series_out})
    time_df.to_excel(writer, sheet_name="Time", index=False)

    # 各工作表：将时间列作为第一列，数据紧随其后
    def write_with_time(df, sheet_name):
        out_df = pd.concat([time_df, df], axis=1)
        out_df.to_excel(writer, sheet_name=sheet_name, index=False)

    write_with_time(temper_b_cali, "Side_Temperature")
    write_with_time(strain_b_cali, "Side_Strain")
    write_with_time(temper_m_cali, "Middle_Temperature")
    write_with_time(strain_m_cali, "Middle_Strain")
    write_with_time(temper_t_cali, "Top_Temperature")
    write_with_time(strain_t_cali, "Top_Strain")

print(f"导出成功！文件保存在：{output_path}")

# =============================================================================
# 10. 绘制曲线图
# =============================================================================
def plot_sensor_data(df, title, ylabel):
    plt.figure(figsize=(12, 6))
    for col in df.columns:
        plt.plot(df.index, df[col], label=col)
    plt.title(title)
    plt.xlabel('Time')
    plt.ylabel(ylabel)
    plt.legend(loc='upper left')
    # 格式化 x 轴时间标签
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    # 固定显示 6 个刻度
    x_min, x_max = df.index.min(), df.index.max()
    ticks = pd.date_range(start=x_min, end=x_max, periods=6)
    plt.gca().set_xticks(ticks)
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', linewidth=0.5, color='gray')
    plt.tight_layout()

plot_sensor_data(temper_b_cali, 'Side Temperature', 'Temperature (℃)')
plot_sensor_data(strain_b_cali, 'Side Strain', 'Strain (με)')
plot_sensor_data(temper_m_cali, 'Middle Temperature', 'Temperature (℃)')
plot_sensor_data(strain_m_cali, 'Middle Strain', 'Strain (με)')
plot_sensor_data(temper_t_cali, 'Top Temperature', 'Temperature (℃)')
plot_sensor_data(strain_t_cali, 'Top Strain', 'Strain (με)')

plt.show()

# =============================================================================
# 输出运行时间
# =============================================================================
end_time = time.time()
run_time = end_time - start_time
print(f"\n代码运行时间：{run_time:.4f} 秒")