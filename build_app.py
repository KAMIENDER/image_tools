import sys
import os
from PyInstaller.__main__ import run


def build_app():
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 设置打包参数
    opts = [
        'video_processor.py',  # 主程序文件
        '--name=VideoProcessor',  # 应用程序名称
        '--onefile',  # 打包成单个可执行文件
        '--windowed',  # 使用GUI模式，不显示控制台窗口
        '--clean',  # 清理临时文件
        '--add-data=app_state.txt:.',  # 添加数据文件
        f'--workpath={os.path.join(current_dir, "build")}',  # 设置工作目录
        f'--distpath={os.path.join(current_dir, "dist")}',  # 设置输出目录
        '--noupx',  # 不使用UPX压缩
    ]

    # 根据操作系统添加特定配置
    if sys.platform.startswith('darwin'):  # macOS
        opts.extend([
            '--codesign-identity=-',  # 跳过代码签名
        ])
    elif sys.platform.startswith('win'):
        opts.extend([
            '--runtime-tmpdir=.',  # 设置运行时临时目录
        ])

    # 运行PyInstaller
    run(opts)


if __name__ == '__main__':
    build_app()
