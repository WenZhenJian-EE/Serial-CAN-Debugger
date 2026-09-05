# -*- coding: utf-8 -*-
"""
Serial-CAN-Debugger V3.0 (串口与 CAN 实时示波器调试上位机) 离线打包流水线
支持双编译器管道:
1. PyInstaller: 开箱即用、依赖全量自动绑定的便携单文件 (25MB~35MB)
2. Nuitka C++: 深度转译为 C/C++ 原生二进制机器码，无 Python 字节码暴露，体积与冷启动速度登峰造极

使用方式:
    python build_exe.py                        # 默认使用 PyInstaller 单文件打包
    python build_exe.py --compiler nuitka       # 使用 Nuitka C++ 机器码编译
    python build_exe.py --skip-webui           # 跳过前端重新构建
"""

import argparse
import os
import shutil
import subprocess
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def build_webui():
    print("\n" + "=" * 60)
    print(" [Step 1/2] 构建现代 WebUI 前端工程 (Vite + Vue 3)")
    print("=" * 60)
    webui_dir = os.path.join(PROJECT_ROOT, "webui")
    if not os.path.exists(os.path.join(webui_dir, "node_modules")):
        print("[*] 正在安装前端依赖包 (npm install)...")
        subprocess.run("npm install", cwd=webui_dir, shell=True, check=True)

    print("[*] 正在执行 Vite 生产环境高压缩构建 (npm run build)...")
    subprocess.run("npm run build", cwd=webui_dir, shell=True, check=True)

    dist_dir = os.path.join(webui_dir, "dist")
    if not os.path.exists(dist_dir) or not os.path.exists(os.path.join(dist_dir, "index.html")):
        raise RuntimeError("WebUI 构建失败: dist/index.html 未生成！")
    print("[+] WebUI 产物落盘成功: webui/dist/")


def package_with_pyinstaller():
    print("\n" + "=" * 60)
    print(" [Step 2/2] 正在调用 PyInstaller 进行便携单文件打包...")
    print("=" * 60)

    webui_dist = os.path.join(PROJECT_ROOT, "webui", "dist")
    main_py = os.path.join(PROJECT_ROOT, "main.py")

    hidden_imports = [
        "uvicorn",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.auto",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespans",
        "uvicorn.lifespans.on",
        "webview",
        "webview.platforms.winforms",
        "webview.platforms.edgechromium",
        "clr",
        "pythonnet",
        "scipy.io",
        "scipy.signal",
        "cantools",
        "serial",
        "can",
        "sqlite3",
        "engineio.async_drivers.asgi",
    ]

    # 排除环境中多余的超重依赖库 (如 PyQt5 / PySide6 / matplotlib / pandas 等)
    exclude_modules = [
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "matplotlib",
        "pandas",
        "PIL",
        "tkinter",
        "IPython",
        "jupyter",
        "notebook",
        "torch",
        "tensorflow",
        "cv2",
    ]

    icon_path = os.path.join(PROJECT_ROOT, "app_icon.ico")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "Serial-CAN-Debugger",
        "--add-data",
        f"{webui_dist};webui/dist",
    ]
    if os.path.exists(icon_path):
        cmd.extend(["--icon", icon_path])

    for hi in hidden_imports:
        cmd.extend(["--hidden-import", hi])

    for em in exclude_modules:
        cmd.extend(["--exclude-module", em])

    cmd.append(main_py)

    print(f"[*] 执行构建指令: {' '.join(cmd[:8])} ...")
    start_time = time.time()
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
    duration = time.time() - start_time

    dist_exe = os.path.join(PROJECT_ROOT, "dist", "Serial-CAN-Debugger.exe")
    root_exe = os.path.join(PROJECT_ROOT, "Serial-CAN-Debugger.exe")

    # 将生成的单文件可执行程序直接同步覆盖到根目录，确保用户即开即用
    if os.path.exists(dist_exe):
        try:
            shutil.copy2(dist_exe, root_exe)
        except PermissionError:
            print("[*] 检测到根目录 EXE 正被占用，尝试关闭旧进程并重试覆盖...")
            subprocess.run("taskkill /f /im Serial-CAN-Debugger.exe", shell=True, capture_output=True)
            time.sleep(1)
            shutil.copy2(dist_exe, root_exe)

    # 按照极简工作区交付规范，清理打包过程产生的 build/dist 临时文件夹及 .spec 文件
    try:
        build_dir = os.path.join(PROJECT_ROOT, "build")
        dist_dir = os.path.join(PROJECT_ROOT, "dist")
        spec_file = os.path.join(PROJECT_ROOT, "Serial-CAN-Debugger.spec")
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir, ignore_errors=True)
        if os.path.exists(dist_dir):
            shutil.rmtree(dist_dir, ignore_errors=True)
        if os.path.exists(spec_file):
            os.remove(spec_file)
        print("[+] 临时构建产物已彻底清理 (build/, dist/, .spec)")
    except Exception as e:
        print(f"[*] 临时产物清理提示: {e}")

    print_summary("PyInstaller", root_exe, duration)


def package_with_nuitka():
    print("\n" + "=" * 60)
    print(" [Step 2/2] 正在调用 Nuitka C++ 进行原生机器码深度编译...")
    print("=" * 60)

    # 检查 Nuitka 是否就绪
    try:
        ver_res = subprocess.run([sys.executable, "-m", "nuitka", "--version"], capture_output=True, text=True)
        if ver_res.returncode != 0:
            raise FileNotFoundError()
    except Exception:
        print("[-] 系统中未检测到 Nuitka。可通过以下指令进行安装后重试:")
        print("    pip install nuitka zstandard ordered-set")
        print("[*] 自动切换至 PyInstaller 进行构建...")
        package_with_pyinstaller()
        return

    webui_dist = os.path.join(PROJECT_ROOT, "webui", "dist")
    main_py = os.path.join(PROJECT_ROOT, "main.py")

    cmd = [
        sys.executable,
        "-m",
        "nuitka",
        "--standalone",
        "--onefile",
        "--windows-disable-console",
        "--enable-plugin=pywebview",
        f"--include-data-dir={webui_dist}=webui/dist",
        "--output-filename=Serial-CAN-Debugger.exe",
        "--output-dir=dist",
    ]

    icon_path = os.path.join(PROJECT_ROOT, "app_icon.ico")
    if os.path.exists(icon_path):
        cmd.append(f"--windows-icon-from-ico={icon_path}")

    cmd.append(main_py)

    print(f"[*] 执行 Nuitka 指令: {' '.join(cmd[:8])} ...")
    start_time = time.time()
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
    duration = time.time() - start_time

    dist_exe = os.path.join(PROJECT_ROOT, "dist", "Serial-CAN-Debugger.exe")
    root_exe = os.path.join(PROJECT_ROOT, "Serial-CAN-Debugger.exe")
    if os.path.exists(dist_exe):
        shutil.copy2(dist_exe, root_exe)

    print_summary("Nuitka C++", root_exe, duration)


def print_summary(compiler_name, exe_path, duration):
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print("\n" + "=" * 65)
        print(f" [+] SUCCESS: 极速单文件交付产物已成功生成！[编译器: {compiler_name}]")
        print(f"     交付路径: {exe_path}")
        print(f"     可执行体积: {size_mb:.2f} MB (相比旧版 Electron 173.9 MB 缩减 >80%)")
        print(f"     构建总耗时: {duration:.1f} 秒")
        print("=" * 65 + "\n")
    else:
        print("[-] 构建已执行，但在指定路径未找到目标可执行文件。")


def main():
    parser = argparse.ArgumentParser(description="Serial-CAN-Debugger 离线单文件打包工具")
    parser.add_argument(
        "--compiler",
        choices=["pyinstaller", "nuitka"],
        default="pyinstaller",
        help="打包编译器选择: pyinstaller (默认) 或 nuitka (C++ 原生编译)",
    )
    parser.add_argument(
        "--skip-webui",
        action="store_true",
        help="跳过 WebUI 前端重新编译",
    )
    args = parser.parse_args()

    try:
        if not args.skip_webui:
            build_webui()
        else:
            print("[*] 跳过 WebUI 编译步骤，使用现有 webui/dist 产物。")

        if args.compiler == "nuitka":
            package_with_nuitka()
        else:
            package_with_pyinstaller()
    except Exception as e:
        print(f"\n[-] 打包异常终止: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
