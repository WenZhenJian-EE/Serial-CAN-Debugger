# -*- coding: utf-8 -*-
"""
文件名: desktop/window.py
pywebview 原生桌面宿主窗口、动态高位端口监听与 DesktopApi JS Bridge
"""

import os
import socket
import sys
import threading
import time
import webbrowser
from typing import Optional

import uvicorn
import webview


def find_free_port(start_port: int = 18000, max_port: int = 19000) -> int:
    """动态扫描并分配空闲高位 TCP 端口，彻底避免端口冲突"""
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return 8000


class DesktopApi:
    """JS Bridge: 暴露给前端 window.pywebview.api 的系统级原生能力"""

    def __init__(self, port: int):
        self._port = port
        self._window = None

    def _set_window(self, window):
        self._window = window

    def get_server_port(self) -> int:
        return self._port

    def choose_file(self, title: str = "选择文件", file_types: tuple = ("DBC 文件 (*.dbc)", "CSV 文件 (*.csv)", "所有文件 (*.*)")) -> Optional[str]:
        """打开系统原生文件选择对话框"""
        if not self._window:
            return None
        res = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=file_types
        )
        if res and len(res) > 0:
            return res[0]
        return None

    def save_file(self, title: str = "保存文件", default_name: str = "export.csv", file_types: tuple = ("CSV 文件 (*.csv)", "MAT 文件 (*.mat)", "所有文件 (*.*)")) -> Optional[str]:
        """打开系统原生文件保存对话框"""
        if not self._window:
            return None
        res = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=default_name,
            file_types=file_types
        )
        return res

    def choose_folder(self, title: str = "选择文件夹") -> Optional[str]:
        """打开系统原生文件夹选择对话框"""
        if not self._window:
            return None
        res = self._window.create_file_dialog(webview.FOLDER_DIALOG)
        if res and len(res) > 0:
            return res[0]
        return None

    def open_external_url(self, url: str):
        """在系统默认浏览器中打开外部链接"""
        webbrowser.open(url)

    def open_local_path(self, path: str):
        """在 Windows 资源管理器中打开指定目录或高亮文件"""
        if os.path.exists(path):
            os.system(f'explorer /select,"{os.path.abspath(path)}"')

    def get_system_info(self) -> dict:
        return {
            "app_name": "Serial-CAN-Debugger",
            "version": "3.0.0",
            "runtime": "Edge WebView2 DirectComposition GPU Accelerated",
            "python_version": sys.version.split()[0],
            "port": self._port,
        }


def start_server_thread(port: int):
    """在后台独立守护线程中启动 FastAPI Uvicorn 回环服务"""
    from server.api import app
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    return server


def wait_for_server(port: int, timeout: float = 10.0) -> bool:
    """轮询等待本地服务启动就绪"""
    import urllib.request
    url = f"http://127.0.0.1:{port}/health"
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=0.5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.05)
    return False


def run_desktop(port: Optional[int] = None, debug: bool = False):
    """拉起 pywebview 宿主桌面应用"""
    if port is None:
        port = find_free_port()

    print(f"[Desktop] Launching local FastAPI backend on 127.0.0.1:{port} ...")
    start_server_thread(port)

    if not wait_for_server(port):
        print(f"[Desktop] Error: Backend failed to start on port {port}")
        return

    print(f"[Desktop] Backend is healthy. Creating WebView2 native window...")
    api = DesktopApi(port)

    window = webview.create_window(
        title="Serial-CAN-Debugger V3.0",
        url=f"http://127.0.0.1:{port}",
        width=1440,
        height=900,
        min_size=(1024, 680),
        background_color="#121214",
        js_api=api,
        text_select=True,
    )
    api._set_window(window)

    # 启动 pywebview 主循环，强制指定 Windows Edge Chromium 常青内核
    webview.start(
        gui="edgechromium",
        debug=debug,
    )
