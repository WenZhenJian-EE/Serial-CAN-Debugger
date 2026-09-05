# -*- coding: utf-8 -*-
"""
Local High-Speed Bus (高速本地总线与业务接口层)
基于 FastAPI + WebSocket 实现毫秒级本地回环
"""

from .api import create_app

__all__ = ["create_app"]
