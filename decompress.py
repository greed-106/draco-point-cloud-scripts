import os
import re
import time
import argparse
import numpy as np
from pathlib import Path
import open3d as o3d
import DracoPy


def natural_sort_key(s):
    """自然排序文件名"""
    _nsre = re.compile(r'(\d+)')
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, str(s))]


def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='点云解码工具')
    parser.add_argument('--input_dir', type=str, required=True, help='包含DRC文件的输入目录')
    parser.add_argument('--output_dir', type=str, required=True, help='PLY输出目录')

    args = parser.parse_args()

    # 配置参数
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    # 验证输入目录
    if not input_dir.exists():
        print(f"❌ 错误：输入目录不存在 {input_dir}")
        return

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 获取排序后的DRC文件
    drc_files = sorted(
        [f for f in input_dir.glob('*.drc') if f.is_file()],
        key=lambda x: natural_sort_key(x.name)
    )

    # 初始化统计
    stats = {
        'total': len(drc_files),
        'success': 0,
        'fail': 0,
        'total_time': 0.0,
        'input_size': 0.0,
        'output_size': 0.0
    }

    print(f"🔧 开始解码 - 共 {stats['total']} 个文件")
    start_all = time.perf_counter()
    decode_time = 0

    for idx, drc_path in enumerate(drc_files, 1):
        file_start = time.perf_counter()
        try:
            # 读取并解码DRC文件
            with open(drc_path, 'rb') as f:
                data = DracoPy.decode(f.read())

            # 创建Open3D点云对象
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(data.points)

            duration = time.perf_counter() - file_start
            decode_time += duration

            # 添加颜色信息
            if data.colors is not None:
                pcd.colors = o3d.utility.Vector3dVector(data.colors[:, :3].astype(np.float32) / 255.0)

            # 构建输出路径
            ply_path = output_dir / f"{drc_path.stem}.ply"

            # 保存为文本格式PLY
            o3d.io.write_point_cloud(
                str(ply_path),
                pcd,
                write_ascii=True,
                compressed=False
            )

            # 计算统计信息

            stats['success'] += 1
            stats['total_time'] += duration

            # 打印进度
            progress = f"[{idx}/{stats['total']}] {drc_path.name.ljust(10)}"
            print(f"{progress} → {ply_path.name} | 耗时: {duration:.4f}s")

        except Exception as e:
            stats['fail'] += 1
            print(f"❌ 文件 {drc_path.name} 解码失败: {str(e)}")
            continue

    # 生成统计报告
    total_wall_time = time.perf_counter() - start_all
    print("\n" + "=" * 60)
    print(f"解码完成 ({stats['success']}/{stats['total']})")
    print("-" * 60)
    print(f"总耗时:     {decode_time:.4f}s")
    print(f"解码帧率:   {stats['success'] / decode_time:.4f} FPS")
    print("=" * 60)


if __name__ == "__main__":
    main()