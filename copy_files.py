import os
import shutil

# ================== 用户自定义路径（请修改为实际路径）==================
SOURCE_DIR = r"E:\Documents\BYD电池测试\数据文件"   # 包含多个二级文件夹的源目录
DEST_DIR   = r"G:\电池数据"     # 目标目录，存放复制出来的文件
# =====================================================================

def copy_matching_excel_files(src_root, dst_root):
    """
    遍历 src_root 下的所有子文件夹，复制与文件夹同名的 Excel 文件到 dst_root。
    """
    # 如果目标文件夹不存在则创建
    if not os.path.exists(dst_root):
        os.makedirs(dst_root)
        print(f"已创建目标文件夹: {dst_root}")

    # 遍历源文件夹下的所有项目
    for item in os.listdir(src_root):
        folder_path = os.path.join(src_root, item)

        # 只处理二级文件夹，跳过文件
        if not os.path.isdir(folder_path):
            continue

        folder_name = item
        copied = False

        # 按优先级尝试常见的 Excel 扩展名
        for ext in ['.xlsx', '.xls', '.xlsm']:
            file_name = folder_name + ext
            file_path = os.path.join(folder_path, file_name)

            if os.path.isfile(file_path):
                dest_path = os.path.join(dst_root, file_name)
                try:
                    shutil.copy2(file_path, dest_path)
                    print(f"已复制: {file_path} -> {dest_path}")
                    copied = True
                    break   # 找到并复制后停止尝试其他扩展名
                except Exception as e:
                    print(f"复制失败: {file_path}，错误: {e}")
                    copied = True   # 标记为已处理，避免警告
                    break

        if not copied:
            print(f"警告: 在 '{folder_path}' 中未找到与文件夹名 '{folder_name}' 匹配的 Excel 文件")

if __name__ == "__main__":
    copy_matching_excel_files(SOURCE_DIR, DEST_DIR)
    print("操作完成。")