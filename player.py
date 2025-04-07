import os
import open3d as o3d
import time
import re
import argparse

def natural_sort_key(s):
    """自然排序辅助函数"""
    _nsre = re.compile('([0-9]+)')
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)]

def main():
    parser = argparse.ArgumentParser(description='PLY点云播放器')
    parser.add_argument('-i', '--input_dir', required=True, help='PLY文件目录路径')
    parser.add_argument('-d', '--delay', type=float, default=0.05,
                       help='帧间隔时间（秒），默认0.05')
    parser.add_argument('-c', '--color', nargs=3, type=float, default=[0.5, 0.5, 0.5],
                       metavar=('R', 'G', 'B'), help='默认颜色RGB值（0-1），默认0.5 0.5 0.5')
    args = parser.parse_args()

    # 获取并排序PLY文件
    ply_files = [
        os.path.join(args.input_dir, f)
        for f in os.listdir(args.input_dir)
        if f.lower().endswith('.ply')
    ]
    ply_files.sort(key=lambda x: natural_sort_key(os.path.basename(x)))

    # 初始化可视化器
    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name='点云播放器', width=1280, height=720)
    point_cloud = o3d.geometry.PointCloud()
    vis.add_geometry(point_cloud)

    # 设置渲染参数
    ctr = vis.get_view_control()
    ctr.set_zoom(0.1)  # 初始缩放级别

    try:
        for file_path in ply_files:
            pcd = o3d.io.read_point_cloud(file_path)

            # 更新点云属性
            point_cloud.points = pcd.points
            if pcd.has_colors():
                point_cloud.colors = pcd.colors
            else:
                point_cloud.colors = o3d.utility.Vector3dVector(
                    [args.color] * len(pcd.points)
                )

            # 自动调整视角（首次帧）
            if ply_files.index(file_path) == 0:
                vis.reset_view_point(True)

            # 更新渲染
            vis.update_geometry(point_cloud)
            vis.poll_events()
            vis.update_renderer()
            print(f"当前帧: {file_path}")
            time.sleep(args.delay)
    finally:
        vis.destroy_window()

if __name__ == "__main__":
    main()