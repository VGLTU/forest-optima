#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Запуск веб-сервера программного комплекса «Лес-Оптима».
"""

import os
import uvicorn

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8890"))
    uvicorn.run("forest_optima.web.app:app", host=host, port=port, reload=False)
