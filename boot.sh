#!/bin/bash
# 换源安装依赖（为了速度快）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
# 启动应用
python server.py
