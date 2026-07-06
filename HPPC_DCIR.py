import pandas as pd

# ==================== 自定义变量区（请根据实际文件修改） ====================
FILE_PATH = r"E:\Documents\BYD电池测试\数据文件1\20260324_HPPC_50cycle\20260324_HPPC_50cycle.xlsx"         # Excel 文件路径
SHEET_NAME = "step"                     # 源数据工作表名称，None 表示自动使用第一个工作表
CURRENT = 170                         # 充放电电流（绝对值），单位 A
OUTPUT_SHEET = "DCIR_Results"         # 写入源文件的新工作表名称

# 列索引（0-based，对应 Excel 的 A=0, B=1, ...）
COL_CYCLE = 0                         # A列：循环号
COL_STEP  = 1                         # B列：工步号
COL_V_START = 9                       # J列：起始电压 (V)
COL_V_END   = 10                      # K列：结束电压 (V)
# ============================================================================

def main():
    # ---------- 读取数据 ----------
    if SHEET_NAME is None:
        xls = pd.ExcelFile(FILE_PATH)
        sheet = xls.sheet_names[0]
        print(f"未指定工作表，自动使用第一个工作表：{sheet}")
    else:
        sheet = SHEET_NAME

    df = pd.read_excel(FILE_PATH, sheet_name=sheet, header=0)

    # 提取需要的列，并重命名便于处理
    data = df.iloc[:, [COL_CYCLE, COL_STEP, COL_V_START, COL_V_END]].copy()
    data.columns = ["cycle", "step", "V_start", "V_end"]

    # ---------- 提取关键工步的电压 ----------
    # 工步4 结束电压 -> 充电脉冲前的静置电压
    rest_before_charge = data[data["step"] == 4][["cycle", "V_end"]].rename(
        columns={"V_end": "V_rest_before_charge"}
    )
    # 工步5 起始电压 -> 充电脉冲开始瞬间电压
    charge_pulse = data[data["step"] == 5][["cycle", "V_start"]].rename(
        columns={"V_start": "V_charge_start"}
    )
    # 工步6 结束电压 -> 放电脉冲前的静置电压
    rest_before_discharge = data[data["step"] == 6][["cycle", "V_end"]].rename(
        columns={"V_end": "V_rest_before_discharge"}
    )
    # 工步7 起始电压 -> 放电脉冲开始瞬间电压
    discharge_pulse = data[data["step"] == 7][["cycle", "V_start"]].rename(
        columns={"V_start": "V_discharge_start"}
    )

    # ---------- 按循环号合并数据 ----------
    result = rest_before_charge.merge(charge_pulse, on="cycle", how="inner")
    result = result.merge(rest_before_discharge, on="cycle", how="inner")
    result = result.merge(discharge_pulse, on="cycle", how="inner")

    if result.empty:
        raise ValueError("未能根据工步4/5/6/7构建完整数据，请检查列索引或工作表内容。")

    # ---------- 计算内阻 ----------
    result["R_charge"] = (
        result["V_charge_start"] - result["V_rest_before_charge"]
    ) / CURRENT

    result["R_discharge"] = (
        result["V_rest_before_discharge"] - result["V_discharge_start"]
    ) / CURRENT

    # 推算 SOC（循环号1对应90% SOC，每次递减10%）
    result["SOC"] = 100 - result["cycle"] * 10

    # 整理输出列
    output = result[["cycle", "SOC", "R_charge", "R_discharge"]].sort_values("cycle")

    # ---------- 控制台输出 ----------
    print("HPPC 直流内阻计算结果：")
    print(output.to_string(index=False, float_format=lambda x: f"{x:.6f}"))

    # ---------- 写入源文件的新工作簿 ----------
    # 注意：需要 openpyxl 引擎，模式为 'a'（追加），如果存在同名工作表则替换
    try:
        with pd.ExcelWriter(FILE_PATH, mode='a', if_sheet_exists='replace', engine='openpyxl') as writer:
            output.to_excel(writer, sheet_name=OUTPUT_SHEET, index=False)
        print(f"结果已写入源文件的新工作表：{OUTPUT_SHEET}")
    except Exception as e:
        print(f"写入源文件失败：{e}")
        print("请检查源文件是否已关闭、openpyxl 库是否安装，或者尝试手动将 CSV 结果导入 Excel。")

if __name__ == "__main__":
    main()