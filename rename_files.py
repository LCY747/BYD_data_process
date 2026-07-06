import os
import re

# ================== 用户自定义路径（请修改为实际路径）==================
PARENT_DIR = r"E:\Documents\test"  # 包含多个二级文件夹的父目录
# =====================================================================

def rename_xlsx_in_subfolders(parent_dir):
    """
    遍历 parent_dir 下的所有子文件夹，将符合条件的 .xlsx 文件重命名为文件夹名。
    条件：文件名（不含扩展名）仅由数字和 '-' 组成，如 '230187-1-1-362.xlsx'。
    """
    if not os.path.isdir(parent_dir):
        print(f"错误: 路径不存在或不是文件夹: {parent_dir}")
        return

    # 正则：只包含数字和 '-' 的文件名
    pattern = re.compile(r'^[\d\-]+\.xlsx$')

    for folder_name in os.listdir(parent_dir):
        folder_path = os.path.join(parent_dir, folder_name)

        # 跳过非文件夹项目
        if not os.path.isdir(folder_path):
            continue

        # 收集当前文件夹内所有符合条件的 .xlsx 文件
        matched_files = [
            f for f in os.listdir(folder_path)
            if pattern.match(f) and os.path.isfile(os.path.join(folder_path, f))
        ]

        if len(matched_files) == 0:
            print(f"警告: 文件夹 '{folder_name}' 中未找到符合条件的 .xlsx 文件，跳过。")
            continue
        elif len(matched_files) > 1:
            print(f"警告: 文件夹 '{folder_name}' 中找到多个符合条件的文件 {matched_files}，请手动处理，跳过。")
            continue

        # 只有一个符合条件的文件，准备重命名
        old_file = matched_files[0]
        old_path = os.path.join(folder_path, old_file)
        new_name = folder_name + ".xlsx"
        new_path = os.path.join(folder_path, new_name)

        if old_file == new_name:
            print(f"文件 '{old_file}' 名称已与文件夹一致，无需重命名。")
            continue

        # 避免覆盖已存在的目标文件
        if os.path.exists(new_path):
            print(f"错误: 目标文件 '{new_name}' 在 '{folder_name}' 中已存在，无法重命名 '{old_file}'，跳过。")
            continue

        try:
            os.rename(old_path, new_path)
            print(f"已重命名: {os.path.join(folder_name, old_file)} -> {os.path.join(folder_name, new_name)}")
        except Exception as e:
            print(f"重命名失败: {os.path.join(folder_name, old_file)}，错误: {e}")

if __name__ == "__main__":
    rename_xlsx_in_subfolders(PARENT_DIR)
    print("操作完成。")