#!/bin/bash

# 设置输入和输出文件路径
#M2D_FILE="D:\AAA_PIC\Parser\MCL_PLYParser\src\data\BWO1\BWO1.m2d"
#TXT_FILE="D:\AAA_PIC\Parser\MCL_PLYParser\src\data\BWO1\workdir\BWO1.txt"

M2D_FILE="D:\AAA_PIC\Parser\MCL_PLYParser\src\data\TestCMD\MILO.m2d"
jsonl_file="D:\AAA_PIC\Parser\MCL_PLYParser\src\data\TestCMD\workdir\MILO.jsonl"

test=false

# 运行预处理脚本
echo "输入文件为: $M2D_FILE"
python src/mcl_preprocess.py "$M2D_FILE"
python src/route/route.py "$jsonl_file"


