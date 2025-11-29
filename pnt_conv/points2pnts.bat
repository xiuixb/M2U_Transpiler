@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ===========================================
:: 将 points.txt 反向转换为 pnts.txt
:: ===========================================

set "input=points.txt"
set "output=pnts_output.txt"

if not exist "%input%" (
    echo 未找到输入文件 %input%
    pause
    exit /b
)

:: 清空输出文件并写入开头 [
break > "%output%"
echo [>>"%output%"

set /a count=0
set "merged="

for /f "usebackq tokens=* delims=" %%A in ("%input%") do (
    set /a count+=1
    set "line=%%A"
    :: 去掉首尾空格
    for /f "tokens=* delims= " %%B in ("!line!") do set "line=%%B"
    if defined merged (
        set "merged=!merged!  !line!"
    ) else (
        set "merged=!line!"
    )

    if !count! EQU 4 (
        >>"%output%" echo !merged!
        set "count=0"
        set "merged="
    )
)

:: 若最后不足4行也要写入
if not "!merged!"=="" (
    >>"%output%" echo !merged!
)

:: 写入结尾 ]
echo ]>>"%output%"

echo 处理完成
echo 输出文件: %output%
pause
