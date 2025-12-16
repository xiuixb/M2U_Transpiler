@echo off
setlocal enabledelayedexpansion

REM 设置源目录
set "src_dir=D:\AAA_PIC\Parser\MCL_PLYParser\llm_refer\backend"
REM 设置输出文件
set "out_file=%src_dir%\all_code.txt"

REM 如果存在旧文件则删除
if exist "%out_file%" del "%out_file%"

REM 遍历所有.py文件
for /r "%src_dir%" %%f in (*.py) do (
    echo ############  %%~nxf  ############ >> "%out_file%"
    type "%%f" >> "%out_file%"
    echo. >> "%out_file%"
    echo. >> "%out_file%"
)

echo All python files merged into "%out_file%"
pause
