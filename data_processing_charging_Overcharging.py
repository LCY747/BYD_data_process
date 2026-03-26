# 第三方库导入
import glob
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import re
import os
import time

start_time = time.time()
# =============================================================================
# 数据导入：整体全部导入，在波长解耦哪步再进行分组区分
# =============================================================================
file_path = r"E:\Documents\BYD电池测试\数据文件\20260317_50_cycle\39_50_cycle"    # 文件路径
# 获取当前文件路径下所有的txt文件
txt_files = glob.glob(f"{file_path}/*.txt")
# 整合所有txt文件
input_data = []     # 总数据列表初始化
# 依次读取所有的txt文件
for txt_file in txt_files:
    # 一次性读取.txt文件的所有行
    with open(txt_file, 'r', encoding='gbk') as file:
        lines = file.readlines()
    # 按制表符分割
    txt_data = [lines[i].strip().split('\t') for i in range(1,len(lines))]
    # 将当前的数据增加到input_data
    input_data.append(txt_data)
    
merged_data = sum(input_data, [])  # 直接合并

# 提取文件的列标题
with open(txt_files[0], 'r', encoding='gbk') as file:
    lines = file.readlines()
column_titles = [lines[0].strip().split('\t')]



# 拟提取的片段数据
startTime = 20260321104945
endTime =   20260322134318


# =============================================================================
# 光纤传感器波长解耦（温度换算）
# 采用一次函数进行解析
# 初始波长为25℃下的波长，温度灵敏度系数为10pm/℃
# ============================================================================
T0 = 27.5         # 初始温度
k = 10          # 温度灵敏度系数
'''
k_ptab = 10     # CH13侧极耳的温度灵敏度系数
k_ntab = 10     # CH10侧极耳的温度灵敏度系数
'''

#---------------------------------解析参数初始化-------------------------------#
# 温度和应变测量传感器的初始波长
WL0_temper_broadside = np.array([1529.9293	,1531.853	,1533.8734	,1535.8419	,
                                 1537.7964	,1539.7262	,1541.739	,1543.7665	,1545.6947])          # 侧面温度测量的初始波长
WL0_strain_broadside = np.array([1529.9792	,1532.0752	,1534.1012	,1536.0223	,
                                 1538.0215	,1540.0045	,1541.9491	,1543.9012	,1545.8201])          # 侧面应变测量的初始波长

WL0_temper_middle = np.array([1529.8577,1531.8346	,1533.8264	,1535.7863	,1537.7731	,
                            1539.6825	,1541.7218	,1543.6433	,1545.5896])                     # 大面中温度测量的初始波长
WL0_strain_middle = np.array([1530.0032	,1531.9487	,1533.8112	,1535.837	,
                            1537.7677	,1539.8282	,1541.8026	,1543.8116	,1545.7057])          # 大面中应变测量的初始波长

WL0_temper_top = np.array([1529.9009, 1531.8538, 1533.901, 1535.8004 , 1537.8138, 
                             1539.7491, 1541.73, 1543.6338, 1545.6028 ])          # 大面上温度测量的初始波长
WL0_strain_top = np.array([1529.8198	,1531.7773	,1533.6188	,1535.5896	,1537.4503	,
                             1539.5037	,1541.4901	,1543.4701	,1545.5015]) # 大面上应变测量的初始波长


# 提取6根光纤传感器的位置索引
index_FOS1 = [i for i, item in enumerate(column_titles[0]) if any(re.search(rf"\b{ch}\b", item) for ch in ['通道2'])]      # 侧边温度
index_FOS2 = [i for i, item in enumerate(column_titles[0]) if any(re.search(rf"\b{ch}\b", item) for ch in ['通道5'])]      # 侧边应变
index_FOS3 = [i for i, item in enumerate(column_titles[0]) if any(re.search(rf"\b{ch}\b", item) for ch in ['通道1'])]      # 大面中温度
index_FOS4 = [i for i, item in enumerate(column_titles[0]) if any(re.search(rf"\b{ch}\b", item) for ch in ['通道6'])]      # 大面中应变
index_FOS5 = [i for i, item in enumerate(column_titles[0]) if any(re.search(rf"\b{ch}\b", item) for ch in ['通道0'])]      # 大面上温度
index_FOS6 = [i for i, item in enumerate(column_titles[0]) if any(re.search(rf"\b{ch}\b", item) for ch in ['通道8'])]      # 大面上应变


#-------------------------------数据存储数组初始化------------------------------#
# 获取数据行数
n_rows = len(merged_data)
n_cols = 9

# 侧壁数据
Converted_temper_broadside = np.zeros((n_rows, n_cols))
Converted_strain_broadside = np.zeros((n_rows, n_cols))

# 大面中数据
Converted_temper_middle = np.zeros((n_rows, n_cols))
Converted_strain_middle = np.zeros((n_rows, n_cols))

# 大面上数据
Converted_temper_top = np.zeros((n_rows, n_cols))
Converted_strain_top = np.zeros((n_rows, n_cols))

# 时间存储初始化
Time_data = []

#---------------------------------光纤传感器数据解析----------------------------#
# 循环处理光纤传感器数据
for i in range(len(merged_data)):
    # 时间数据存储
    Time_data.append(merged_data[i][0])
    
    # 解调仪采集的数据
    current_FBG_data = np.array(merged_data[i])
    # 判断数据是否满足要求（数据总列数）
    if len(current_FBG_data) == 128:
        # 侧面温度测量光纤波长数据
        current_WL_temper_broadside = current_FBG_data[index_FOS1][::2].astype(float)
        # 侧面应变测量光纤波长数据
        current_WL_strain_broadside = current_FBG_data[index_FOS2][::2].astype(float)
        # “顶部温度+大面温度”光纤中的顶部波长数据   大面中温度
        current_WL_temper_middle = current_FBG_data[index_FOS3][::2].astype(float)
        # “顶部温度+大面应变”光纤中的顶部波长数据   大面中应变
        current_WL_strain_middle = current_FBG_data[index_FOS4][::2].astype(float)        
        # “顶部温度+大面温度”光纤中的大面温度波长数据  大面上温度
        current_WL_temper_top = current_FBG_data[index_FOS5][::2].astype(float)
        # “顶部温度+大面应变”光纤中的大面应变波长数据   大面上应变
        current_WL_strain_top = current_FBG_data[index_FOS6][::2].astype(float)         
        
        
        # 数据解耦
        # 侧边温度和应变数据解析     计算温度（℃）= 初始温度 + 波长变化量(nm)×1000 / 灵敏度(10 pm/℃)。
        #                          扣除温度影响后的应变（με）= [（应变波长变化）－（温度波长变化）] ×1000。


        Converted_temper_broadside[i,:] = T0 + (current_WL_temper_broadside - WL0_temper_broadside)*1000/k        
        Converted_strain_broadside[i,:] = ((current_WL_strain_broadside - WL0_strain_broadside) - (current_WL_temper_broadside - WL0_temper_broadside))*1000
        
        # 大面中温度和应变数据解析
        Converted_temper_middle[i,:] = T0 + (current_WL_temper_middle - WL0_temper_middle)*1000/k
        Converted_strain_middle[i,:] = ((current_WL_strain_middle - WL0_strain_middle) - (current_WL_temper_middle - WL0_temper_middle))*1000    
        
        # 大面上温度和应变数据解析
        Converted_temper_top[i,:] = T0 + (current_WL_temper_top - WL0_temper_top)*1000/k        
        Converted_strain_top[i,:] = ((current_WL_strain_top - WL0_strain_top) - (current_WL_temper_top - WL0_temper_top))*1000

    else:
        # 侧边温度和应变数据解析
        Converted_temper_broadside[i,:] = np.nan        
        Converted_strain_broadside[i,:] = np.nan 
        
        # 顶部正负极耳温度数据解析
        Converted_temper_middle[i,:] = np.nan    
        Converted_strain_middle[i,:] = np.nan 
        
        # 大面温度和应变数据解析
        Converted_temper_top[i,:] = np.nan 
        Converted_strain_top[i,:] = np.nan 
        
        continue


# =============================================================================
# 对数据进一步处理，
# 空值插值处理：通过插值进行补充
# 电池运行数据片段提取
# =============================================================================
raw_time_data = np.array(Time_data)
# 将绝对时间转换为相对时间，便于计算香农熵变化率
# 将时间转换成列表形式，以便进行加减
time_obj_list = [datetime.strptime(time_str, "%Y/%m/%d/%H:%M:%S.%f") for time_str in raw_time_data]
# 将时间格式“%Y/%m/%d %H:%M:%S:%f”转换为“%Y%m%d%H%M%S”
time_trans = np.array([time.strftime("%Y%m%d%H%M%S") for time in time_obj_list]).astype(float)
# 将时间转换为以秒为单位，并存储在列表中
time_sec_array = np.array([time_obj.timestamp() for time_obj in time_obj_list])
# 转换后的相对时间为
time_relative = time_sec_array-time_sec_array[0]
# 计算采样步之间的时间差
diff_time_relative = np.diff(time_relative)


#----------------------------------数据异常值处理------------------------------#
# 侧壁数据
interp_temper_broadside = Converted_temper_broadside.copy()
interp_temper_broadside[abs(interp_temper_broadside)  > 10000] = np.nan
interp_strain_broadside = Converted_strain_broadside.copy()
interp_strain_broadside[abs(interp_strain_broadside)  > 10000] = np.nan

# 大面中数据
interp_temper_middle = Converted_temper_middle.copy()
interp_temper_middle[abs(interp_temper_middle)  > 10000] = np.nan
interp_strain_middle = Converted_strain_middle.copy()
interp_strain_middle[abs(interp_strain_middle)  > 10000] = np.nan

# 大面上数据
interp_temper_top = Converted_temper_top.copy()
interp_temper_top[abs(interp_temper_top)  > 10000] = np.nan
interp_strain_top = Converted_strain_top.copy()
interp_strain_top[abs(interp_strain_top)  > 10000] = np.nan


#异常值处理替换代码

def interpolate_columns(data_array, time_array):
    """对 data_array 的每一列进行线性插值填充 NaN（使用 time_array 作为自变量）"""
    for col in range(data_array.shape[1]):
        if np.isnan(data_array[:, col]).any():
            nan_idx = np.where(np.isnan(data_array[:, col]))[0]
            valid = ~np.isnan(data_array[:, col])
            # 直接插值，若 valid 全为空（全NaN列）则 np.interp 会抛出 ValueError，与原代码行为一致
            data_array[nan_idx, col] = np.interp(
                time_array[nan_idx], 
                time_array[valid], 
                data_array[valid, col]
            )

# 对六个数组依次执行插值
interpolate_columns(interp_temper_broadside, time_sec_array)
interpolate_columns(interp_strain_broadside, time_sec_array)
interpolate_columns(interp_temper_middle, time_sec_array)
interpolate_columns(interp_strain_middle, time_sec_array)
interpolate_columns(interp_temper_top, time_sec_array)
interpolate_columns(interp_strain_top, time_sec_array)

'''
# 侧面和大面中异常值处理
for i in range(interp_temper_broadside.shape[1]):
    if np.isnan(interp_temper_broadside[:,i]).any():
        # 提取当前列中空值的行索引
        nan_indices = np.where(np.isnan(interp_temper_broadside[:,i]))
        # 根据行索引寻找插值位置
        interp_position = time_sec_array[nan_indices]
        # 移除存在空值的行，初始化插值函数的x,y
        valid_indices = ~np.isnan(interp_temper_broadside[:,i])
        x_values = time_sec_array[valid_indices]
        y_values = interp_temper_broadside[valid_indices,i]
        
        # 使用线性插值填充空值
        interp_values = np.interp(interp_position,x_values,y_values)
        
        # 将插值结果填入原数组
        interp_temper_broadside[nan_indices,i] = interp_values
        
    if np.isnan(interp_strain_broadside[:,i]).any():
        # 提取当前列中空值的行索引
        nan_indices = np.where(np.isnan(interp_strain_broadside[:,i]))
        # 根据行索引寻找插值位置
        interp_position = time_sec_array[nan_indices]
        # 移除存在空值的行，初始化插值函数的x,y
        valid_indices = ~np.isnan(interp_strain_broadside[:,i])
        x_values = time_sec_array[valid_indices]
        y_values = interp_strain_broadside[valid_indices,i]
        
        # 使用线性插值填充空值
        interp_values = np.interp(interp_position,x_values,y_values)
        
        # 将插值结果填入原数组
        interp_strain_broadside[nan_indices,i] = interp_values
        
    if np.isnan(interp_temper_middle[:,i]).any():
        # 提取当前列中空值的行索引
        nan_indices = np.where(np.isnan(interp_temper_middle[:,i]))
        # 根据行索引寻找插值位置
        interp_position = time_sec_array[nan_indices]
        # 移除存在空值的行，初始化插值函数的x,y
        valid_indices = ~np.isnan(interp_temper_middle[:,i])
        x_values = time_sec_array[valid_indices]
        y_values = interp_temper_middle[valid_indices,i]
        
        # 使用线性插值填充空值
        interp_values = np.interp(interp_position,x_values,y_values)
        
        # 将插值结果填入原数组
        interp_temper_middle[nan_indices,i] = interp_values

    if np.isnan(interp_strain_middle[:,i]).any():
        # 提取当前列中空值的行索引
        nan_indices = np.where(np.isnan(interp_strain_middle[:,i]))
        # 根据行索引寻找插值位置
        interp_position = time_sec_array[nan_indices]
        # 移除存在空值的行，初始化插值函数的x,y
        valid_indices = ~np.isnan(interp_strain_middle[:,i])
        x_values = time_sec_array[valid_indices]
        y_values = interp_strain_middle[valid_indices,i]
        
        # 使用线性插值填充空值
        interp_values = np.interp(interp_position,x_values,y_values)
        
        # 将插值结果填入原数组
        interp_strain_middle[nan_indices,i] = interp_values

# 大面上异常数处据理
for i in range(interp_temper_top.shape[1]):
    if np.isnan(interp_temper_top[:,i]).any():
        # 提取当前列中空值的行索引
        nan_indices = np.where(np.isnan(interp_temper_top[:,i]))
        # 根据行索引寻找插值位置
        interp_position = time_sec_array[nan_indices]
        # 移除存在空值的行，初始化插值函数的x,y
        valid_indices = ~np.isnan(interp_temper_top[:,i])
        x_values = time_sec_array[valid_indices]
        y_values = interp_temper_top[valid_indices,i]
        
        # 使用线性插值填充空值
        interp_values = np.interp(interp_position,x_values,y_values)
        
        # 将插值结果填入原数组
        interp_temper_top[nan_indices,i] = interp_values
        
    if np.isnan(interp_strain_top[:,i]).any():
        # 提取当前列中空值的行索引
        nan_indices = np.where(np.isnan(interp_strain_top[:,i]))
        # 根据行索引寻找插值位置
        interp_position = time_sec_array[nan_indices]
        # 移除存在空值的行，初始化插值函数的x,y
        valid_indices = ~np.isnan(interp_strain_top[:,i])
        x_values = time_sec_array[valid_indices]
        y_values = interp_strain_top[valid_indices,i]
        
        # 使用线性插值填充空值
        interp_values = np.interp(interp_position,x_values,y_values)
        
        # 将插值结果填入原数组
        interp_strain_top[nan_indices,i] = interp_values
 '''       
        
#--------------------------根据起止时间提取目标片段数据--------------------------#
# # 将数据稀疏为1Hz所在的行
unique_values,first_indices = np.unique(np.floor(time_relative), return_index=True)
# 稀疏后的温度和应变数据
time_trans_1Hz = time_trans[first_indices]

Converted_temperB_1Hz = interp_temper_broadside[first_indices,:]
Converted_strainB_1Hz = interp_strain_broadside[first_indices,:]

Converted_temperM_1Hz = interp_temper_middle[first_indices,:]
Converted_strainM_1Hz = interp_strain_middle[first_indices,:]

Converted_temperT_1Hz = interp_temper_top[first_indices,:]
Converted_strainT_1Hz = interp_strain_top[first_indices,:]


index_operation = np.where((time_trans_1Hz >= startTime) & (time_trans_1Hz <= endTime))[0]

# 最终保存的数据
# 提取当前运行窗口下的数据片段
Time_data_1Hz = raw_time_data[first_indices]
Time_data_operation = Time_data_1Hz[index_operation]
Converted_temperB_operation = Converted_temperB_1Hz[index_operation]
Converted_strainB_operation = Converted_strainB_1Hz[index_operation]

Converted_temperM_operation = Converted_temperM_1Hz[index_operation]
Converted_strainM_operation = Converted_strainM_1Hz[index_operation]

Converted_temperT_operation = Converted_temperT_1Hz[index_operation]
Converted_strainT_operation = Converted_strainT_1Hz[index_operation]


#-------------------------------温度数据归一化----------------------------#
Converted_temperB_operation_cali = Converted_temperB_operation[0,0] + (Converted_temperB_operation - Converted_temperB_operation[0,:])
Converted_temperM_operation_cali = Converted_temperM_operation[0,0] + (Converted_temperM_operation - Converted_temperM_operation[0,:])
Converted_temperT_operation_cali = Converted_temperT_operation[0,0] + (Converted_temperT_operation - Converted_temperT_operation[0,:])

#-------------------------------应变相对变化------------------------------#
Converted_strainB_operation_cali = Converted_strainB_operation - Converted_strainB_operation[0,:] 
Converted_strainM_operation_cali = Converted_strainM_operation - Converted_strainM_operation[0,:] 
Converted_strainT_operation_cali = Converted_strainT_operation - Converted_strainT_operation[0,:] 



#==============================================================================
#将数据导出为excel表格
#==============================================================================
# 工作表1（Time）的列名
time_col_names = ["Time"]  
# 工作表2（Side Temperature）的列名
Side_Temperature_col_names = [
    "FBG1", "FBG2", "FBG3", "FBG4", "FBG5", "FBG6",
    "FBG7", "FBG8", "FBG9"
]
# 工作表3（Side Strain）的列名
Side_Strain_col_names = [
    "FBG1", "FBG2", "FBG3", "FBG4", "FBG5", "FBG6",
    "FBG7", "FBG8", "FBG9"
]
# 工作表4（middle Temperature (Positive)）的列名
Middle_Temperature_col_names = [
    "FBG1", "FBG2", "FBG3", "FBG4", "FBG5", "FBG6",
    "FBG7", "FBG8", "FBG9"
]
# 工作表5（middle Temperature (Negative)）的列名
Middle_strain_col_names = [
    "FBG1", "FBG2", "FBG3", "FBG4", "FBG5", "FBG6",
    "FBG7", "FBG8", "FBG9"
]
# 工作表6（top Temperature）的列名
Top_Temperature_col_names = [
    "FBG1", "FBG2", "FBG3", "FBG4", "FBG5", "FBG6",
    "FBG7", "FBG8", "FBG9"
]
# 工作表7（top Strain）的列名
Top_Strain_col_names = [
    "FBG1", "FBG2", "FBG3", "FBG4", "FBG5", "FBG6",
    "FBG7", "FBG8", "FBG9"
]

# 将数组转为pandas表格
df_time = pd.DataFrame(Time_data_operation, columns=time_col_names)

df_time['Time'] = pd.to_datetime(df_time['Time']).dt.strftime('%Y/%m/%d/%H:%M:%S')   #转换时间格式，精确到秒

df_Side_Temperature0 = pd.DataFrame(Converted_temperB_operation_cali, columns=Side_Temperature_col_names)
df_Side_Strain0 = pd.DataFrame(Converted_strainB_operation_cali, columns=Side_Strain_col_names)
df_Middle_Temperature = pd.DataFrame(Converted_temperM_operation_cali, columns=Middle_Temperature_col_names)
df_Middle_strain = pd.DataFrame(Converted_strainM_operation_cali, columns=Middle_strain_col_names)
df_Top_Temperature0 = pd.DataFrame(Converted_temperT_operation_cali, columns=Top_Temperature_col_names)
df_Top_Strain0 = pd.DataFrame(Converted_strainT_operation_cali, columns=Top_Strain_col_names)


# 将时间数据拼接到其它表格中
# axis=1 表示按列拼接，df_time在前（第一列），其余在后
df_Side_Temperature = pd.concat([df_time, df_Side_Temperature0], axis=1)
df_Side_Strain = pd.concat([df_time, df_Side_Strain0], axis=1)
df_Middle_Temperature = pd.concat([df_time, df_Middle_Temperature], axis=1)
df_Middle_strain = pd.concat([df_time, df_Middle_strain], axis=1)
df_Top_Temperature = pd.concat([df_time, df_Top_Temperature0], axis=1)
df_Top_Strain = pd.concat([df_time, df_Top_Strain0], axis=1)

# 导出到同一个Excel的不同工作表
output_path = os.path.join(file_path, "数据汇总.xlsx")
with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
    # 导出时间数据到工作表1
    df_time.to_excel(writer, sheet_name="Time", index=False)
    # 导出侧面温度数据到工作表2
    df_Side_Temperature.to_excel(writer, sheet_name="Side_Temperature", index=False)
    # 导出侧面压力数据到工作表3
    df_Side_Strain.to_excel(writer, sheet_name="Side_Strain", index=False)
    # 导出大面中的温度数据到工作表4
    df_Middle_Temperature.to_excel(writer, sheet_name="Middle_Temperature", index=False)
    # 导出大面中的应变数据到工作表5
    df_Middle_strain.to_excel(writer, sheet_name="Middle_Strain", index=False)
    # 导出大面上温度数据到工作表6
    df_Top_Temperature.to_excel(writer, sheet_name="Top_Temperature", index=False)
    # 导出大面上压力数据到工作表7
    df_Top_Strain.to_excel(writer, sheet_name="Top_Strain", index=False)
    
print("导出成功！文件保存在Python当前工作目录，文件名为：数据汇总.xlsx")

end_time = time.time()
run_time = end_time - start_time
print(f"\n代码运行时间：{run_time:.4f} 秒")

# =============================================================================
# 图像绘制（目标片段）
# 横坐标时间处理
datetime_dates = pd.to_datetime(Time_data_operation)

# 定义绘图函数，避免重复代码
def plot_sensor_data(data, title, ylabel):
    plt.figure()
    for i in range(data.shape[1]):
        plt.plot(datetime_dates, data[:, i], label=f'{i+1}')
    plt.title(title)
    plt.xlabel('Time')
    plt.ylabel(ylabel)
    plt.legend(loc='upper left')
    # 格式化 x 轴的时间标签
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    # 固定横坐标刻度数量为 6 个
    x_min = mdates.date2num(datetime_dates.min())
    x_max = mdates.date2num(datetime_dates.max())
    ticks = np.linspace(x_min, x_max, 6)
    plt.gca().set_xticks(ticks)
    # 旋转 x 轴标签
    plt.xticks(rotation=45)
    plt.gcf().autofmt_xdate()
    # 添加网格
    plt.grid(True, linestyle='--', linewidth=0.5, color='gray')

# 依次绘制6个图（不立即显示）
plot_sensor_data(Converted_temperB_operation_cali, 'Side Temperature', 'Temperature (℃)')
plot_sensor_data(Converted_strainB_operation_cali, 'Side Strain', 'Strain (με)')
'''
plot_sensor_data(Converted_temperM_operation_cali, 'Middle Temperature', 'Temperature (℃)')
plot_sensor_data(Converted_strainM_operation_cali, 'Middle Strain', 'Strain (με)')
plot_sensor_data(Converted_temperT_operation_cali, 'Top Temperature', 'Temperature (℃)')
plot_sensor_data(Converted_strainT_operation_cali, 'Top Strain', 'Strain (με)')
'''
# 最后统一显示所有图形
plt.show()





'''
# =============================================================================
# 横坐标时间处理
datetime_dates = pd.to_datetime(Time_data_operation)

# 1. 侧面温度数据绘图
plt.figure()
for i in range(Converted_temperB_operation_cali.shape[1]):
    plt.plot(datetime_dates,Converted_temperB_operation_cali[:,i],label = f'{i+1}')
# 标签设置
plt.title('Side Temperature')
plt.xlabel('Time')
plt.ylabel('Temperature (℃)')
plt.legend(loc='upper left')
# 格式化 x 轴的时间标签
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
# 固定横坐标刻度数量为 6 个
x_min = mdates.date2num(datetime_dates.min())
x_max = mdates.date2num(datetime_dates.max())
ticks = np.linspace(x_min, x_max, 6)  # 生成 6 个等间隔的刻度
plt.gca().set_xticks(ticks)
# 旋转 x 轴标签
plt.xticks(rotation=45)
# 自动调整日期标签以防止重叠
plt.gcf().autofmt_xdate()
# 添加网格
plt.grid(True, linestyle='--', linewidth=0.5, color='gray')
plt.show() 


# 2. 侧面应变数据绘图
plt.figure()
for i in range(Converted_strainB_operation.shape[1]):
    plt.plot(datetime_dates,Converted_strainB_operation_cali[:,i],label = f'{i+1}')
# 标签设置
plt.title('Side Strain')
plt.xlabel('Time')
plt.ylabel('Strain (με)')
plt.legend(loc='upper left')
# 格式化 x 轴的时间标签
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
# 固定横坐标刻度数量为 6 个
x_min = mdates.date2num(datetime_dates.min())
x_max = mdates.date2num(datetime_dates.max())
ticks = np.linspace(x_min, x_max, 6)  # 生成 6 个等间隔的刻度
plt.gca().set_xticks(ticks)
# 旋转 x 轴标签
plt.xticks(rotation=45)
# 自动调整日期标签以防止重叠
plt.gcf().autofmt_xdate()
# 添加网格
plt.grid(True, linestyle='--', linewidth=0.5, color='gray')
plt.show() 


# 3. 大面中温度数据（靠近正极）绘图
plt.figure()
for i in range(Converted_temperM_operation_cali.shape[1]):
    plt.plot(datetime_dates,Converted_temperM_operation_cali[:,i],label = f'{i+1}')
# 标签设置
plt.title('Middle Temperature ')
plt.xlabel('Time')
plt.ylabel('Temperature (℃)')
plt.legend(loc='upper left')
# 格式化 x 轴的时间标签
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
# 固定横坐标刻度数量为 6 个
x_min = mdates.date2num(datetime_dates.min())
x_max = mdates.date2num(datetime_dates.max())
ticks = np.linspace(x_min, x_max, 6)  # 生成 6 个等间隔的刻度
plt.gca().set_xticks(ticks)
# 旋转 x 轴标签
plt.xticks(rotation=45)
# 自动调整日期标签以防止重叠
plt.gcf().autofmt_xdate()
# 添加网格
plt.grid(True, linestyle='--', linewidth=0.5, color='gray')
plt.show() 


# 4. 大面中应变数据（靠近负极）绘图
plt.figure()
for i in range(Converted_strainM_operation_cali.shape[1]):
    plt.plot(datetime_dates,Converted_strainM_operation_cali[:,i],label = f'{i+1}')
# 标签设置
plt.title('Middle Strain')
plt.xlabel('Time')
plt.ylabel('Strain (με)')
plt.legend(loc='upper left')
# 格式化 x 轴的时间标签
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
# 固定横坐标刻度数量为 6 个
x_min = mdates.date2num(datetime_dates.min())
x_max = mdates.date2num(datetime_dates.max())
ticks = np.linspace(x_min, x_max, 6)  # 生成 6 个等间隔的刻度
plt.gca().set_xticks(ticks)
# 旋转 x 轴标签
plt.xticks(rotation=45)
# 自动调整日期标签以防止重叠
plt.gcf().autofmt_xdate()
# 添加网格
plt.grid(True, linestyle='--', linewidth=0.5, color='gray')
plt.show() 


# 5. 大面上温度数据绘图
plt.figure()
for i in range(Converted_temperT_operation_cali.shape[1]):
    plt.plot(datetime_dates,Converted_temperT_operation_cali[:,i],label = f'{i+1}')
# 标签设置
plt.title('Top Temperature')
plt.xlabel('Time')
plt.ylabel('Temperature (℃)')
plt.legend(loc='upper left')
# 格式化 x 轴的时间标签
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
# 固定横坐标刻度数量为 6 个
x_min = mdates.date2num(datetime_dates.min())
x_max = mdates.date2num(datetime_dates.max())
ticks = np.linspace(x_min, x_max, 6)  # 生成 6 个等间隔的刻度
plt.gca().set_xticks(ticks)
# 旋转 x 轴标签
plt.xticks(rotation=45)
# 自动调整日期标签以防止重叠
plt.gcf().autofmt_xdate()
# 添加网格
plt.grid(True, linestyle='--', linewidth=0.5, color='gray')
plt.show() 

# 6. 大面上应变数据绘图
plt.figure()
for i in range(Converted_strainT_operation.shape[1]):
    plt.plot(datetime_dates,Converted_strainT_operation_cali[:,i],label = f'{i+1}')
# 标签设置
plt.title('Top Strain')
plt.xlabel('Time')
plt.ylabel('Strain (με)')
plt.legend(loc='upper left')
# 格式化 x 轴的时间标签
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
# 固定横坐标刻度数量为 6 个
x_min = mdates.date2num(datetime_dates.min())
x_max = mdates.date2num(datetime_dates.max())
ticks = np.linspace(x_min, x_max, 6)  # 生成 6 个等间隔的刻度
plt.gca().set_xticks(ticks)
# 旋转 x 轴标签
plt.xticks(rotation=45)
# 自动调整日期标签以防止重叠
plt.gcf().autofmt_xdate()
# 添加网格
plt.grid(True, linestyle='--', linewidth=0.5, color='gray')
plt.show() 
'''






