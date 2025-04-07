import os
import time
import re
import DracoPy
import numpy as np
from pathlib import Path
import argparse


def natural_sort_key(s):
    """自然排序文件名"""
    _nsre = re.compile(r'(\d+)')
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, str(s))]


def read_text_ply(file_path):
    """读取文本格式PLY文件"""
    from plyfile import PlyData  # 需要安装python-plyfile

    ply_data = PlyData.read(file_path)
    vertices = ply_data['vertex']

    # 提取坐标
    points = np.vstack([vertices['x'], vertices['y'], vertices['z']]).T

    # 提取颜色（如果存在）
    colors = None
    if 'red' in vertices.data.dtype.names:
        colors = np.vstack([vertices['red'],
                            vertices['green'],
                            vertices['blue']]).T / 255.0

    return points, colors


def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='点云编码工具')
    parser.add_argument('--input_dir', type=str, help='输入目录路径，包含PLY文件')
    parser.add_argument('--output_dir', type=str, help='输出目录路径，用于保存压缩后的DRC文件')
    parser.add_argument('--qp', type=int, default=8,
                        help='量化位数(quantization_bits)，默认为8')
    parser.add_argument('--cl', type=int, default=10,
                        help='压缩级别(compression_level)，默认为10')

    args = parser.parse_args()

    # 配置参数
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    qp = args.qp
    cl = args.cl

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    # 获取排序后的PLY文件列表
    ply_files = sorted(
        [f for f in input_dir.glob('*.ply') if f.is_file()],
        key=lambda x: natural_sort_key(x.name)
    )

    # 初始化统计
    stats = {
        'total': len(ply_files),
        'success': 0,
        'total_time': 0.0,
        'input_size': 0.0,
        'output_size': 0.0
    }

    print(f"🔧 开始压缩（qp={qp}, cl={cl}）共 {stats['total']} 个文件...")
    start_all = time.perf_counter()
    encode_time = 0

    for idx, ply_path in enumerate(ply_files, 1):
        try:
            # 读取文本PLY
            points, colors = read_text_ply(ply_path)

            # 转换颜色格式（0-255整型）
            if colors is not None:
                colors = (colors * 255).astype(np.uint8)

            # Draco压缩
            start = time.perf_counter()
            compressed = DracoPy.encode(
                points=points.astype(np.float32),
                quantization_bits=qp,
                compression_level=cl
            )

            # 保存压缩文件
            drc_path = output_dir / f"{ply_path.stem}.drc"
            with open(drc_path, 'wb') as f:
                f.write(compressed)

            # 统计信息
            duration = time.perf_counter() - start
            stats['total_time'] += duration
            stats['input_size'] += ply_path.stat().st_size / (1024 ** 2)
            stats['output_size'] += drc_path.stat().st_size / (1024 ** 2)
            stats['success'] += 1
            encode_time += duration

            # 打印进度
            print(f"[{idx}/{stats['total']}] {ply_path.name.ljust(10)}  → {ply_path.stem}.drc"
                  f"| 压缩比: {stats['input_size'] / stats['output_size']:.1f}x "
                  f"| 耗时: {duration:.4f}s")

        except Exception as e:
            print(f"❌ 文件 {ply_path.name} 压缩失败: {str(e)}")
            continue

    # 生成报告
    total_wall_time = time.perf_counter() - start_all
    print("\n" + "=" * 60)
    print(f"压缩完成 ({stats['success']}/{stats['total']})")
    print("-" * 60)
    print(f"编码总耗时:     {encode_time:.4f}s")
    print(f"输入总量:   {stats['input_size']:.2f} MB")
    print(f"输出总量:   {stats['output_size']:.2f} MB")
    print(f"平均压缩比: {stats['input_size'] / stats['output_size']:.1f}x")
    print(f"编码帧率: {stats['success'] / encode_time:.2f} fps")
    print("=" * 60)


if __name__ == "__main__":
    main()