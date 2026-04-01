import os
import sys

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

from src.application.magic2unipic import MAGIC2UNIPIC

import argparse
from pathlib import Path
from multiprocessing import Pool, cpu_count


# ----------------------------------------------------------------------
# 单个文件的转译任务（使用 m2u_pipeline）
# ----------------------------------------------------------------------
def process_one(args):
    input_file, out_dir = args
    input_file = Path(input_file)
    out_dir    = Path(out_dir)

    try:
        m2u = MAGIC2UNIPIC(str(input_file))
        m2u.m2u_pipeline()

        return (str(input_file), True, "OK")

    except Exception as e:
        return (str(input_file), False, f"ERROR: {e}")




# ----------------------------------------------------------------------
# 主批处理
# ----------------------------------------------------------------------
def batch_process(input_files, workers):

    tasks = []
    for input_file in input_files:
        input_file = Path(input_file)
        out_dir = input_file.parent / "Simulation"
        out_dir.mkdir(parents=True, exist_ok=True)
        tasks.append((str(input_file), str(out_dir)))

    results = []
    if workers == 1:
        for t in tasks:
            results.append(process_one(t))
    else:
        with Pool(processes=workers) as pool:
            for r in pool.imap_unordered(process_one, tasks):
                results.append(r)

    # ---- 修复统计部分 ----
    ok_count = sum(1 for (_, ok, _) in results if ok)
    fail_count = len(results) - ok_count

    print("\n================ SUMMARY ================")
    print(f"Total   : {len(results)}")
    print(f"Success : {ok_count}")
    print(f"Failed  : {fail_count}")
    print("=========================================\n")

    return results


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="并行批量运行 MAGIC2UNIPIC 转译流程"
    )
    parser.add_argument("-i", "--input", required=True, nargs="+",
                        help="输入 MAGIC 文件目录")
    parser.add_argument("-w", "--workers", type=int, default=cpu_count(),
                        help="并行进程数（默认 CPU 核数）")

    args = parser.parse_args()

    batch_process(args.input, args.workers)


if __name__ == "__main__":
    main()