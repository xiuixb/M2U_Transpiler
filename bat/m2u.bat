@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 设置源目录（根目录）
set "src_dir=D:\AAA_PIC\Parser\M2U_Transpiler\"
REM 设置输出文件
set "out_file=%src_dir%\m2u_conv_code.txt"

REM 如果存在旧文件则删除
if exist "%out_file%" del "%out_file%"

REM 按顺序拼接指定文件
for %%f in (
    "%src_dir%\config.py"
    "%src_dir%\mcl_conv.py"
    "%src_dir%\all_commands.py"
    "%src_dir%\savefiles.py"
) do (
    if exist "%%f" (
        echo ############  %%~nxf  ############ >> "%out_file%"
        type "%%f" >> "%out_file%"
        echo. >> "%out_file%"
        echo. >> "%out_file%"
    ) else (
        echo [error] 未找到文件 %%f
    )
)

echo [done] 已合并核心 MCL 源文件到 "%out_file%"
pause
