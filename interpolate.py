import pandas as pd
import os
import time

start_time = time.time()

def interpolate_excel(input_file, output_file=None):
    """
    对 Excel 文件中所有工作表的数值列进行线性插值补全缺失值。
    
    参数:
        input_file (str): 输入 Excel 文件路径。
        output_file (str, optional): 输出 Excel 文件路径。若未指定，将在原文件名后添加 "_interpolated"。
    
    返回:
        str: 输出文件路径。
    """
    # 读取所有工作表
    sheets = pd.read_excel(input_file, sheet_name=None, header=0, engine='calamine')
    
    # 生成默认输出文件名
    if output_file is None:
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_interpolated{ext}"
    
    # 使用 ExcelWriter 写入新文件
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        for sheet_name, df in sheets.items():
            # 复制数据框，避免修改原始对象
            df_interp = df.copy()
            
            # 遍历除第一列外的所有列
            for col in df.columns[1:]:
                # 仅对数值型列进行插值
                if pd.api.types.is_numeric_dtype(df[col]):
                    # 线性插值（基于行索引），自动处理每个缺失段
                    df_interp[col] = df[col].interpolate(method='linear')
                # 非数值列（如时间列）保持不变
            
            # 将处理后的工作表写入新文件
            df_interp.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"插值完成，结果已保存至：{output_file}")
    return output_file

# 使用示例
if __name__ == "__main__":
    input_path = "E:\\Documents\\BYD电池测试\\数据文件\\20260315_low_C_Rate\\数据汇总_filtered.xlsx"         # 替换为实际文件路径
    interpolate_excel(input_path)

end_time = time.time()
run_time = end_time - start_time
print(f"\n代码运行时间：{run_time:.4f} 秒")