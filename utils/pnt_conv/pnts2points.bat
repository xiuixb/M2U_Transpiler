@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ===========================================
:: 格式化点坐标文件 (UTF-8)
:: 输入: pnts.txt
:: 输出: points.txt
:: ===========================================

set "input=pnts.txt"
set "output=points_output.txt"

if not exist "%input%" (
    echo 未找到输入文件 %input%
    pause
    exit /b
)

:: ===========================================
:: 第一步：合并所有行（去掉内部换行）
:: ===========================================
set "merged="
for /f "usebackq tokens=* delims=" %%A in ("%input%") do (
    set "line=%%A"
    :: 去掉行首空格
    for /f "tokens=* delims= " %%B in ("!line!") do set "line=%%B"
    if not "!line!"=="" (
        set "merged=!merged! !line!"
    )
)

:: 去掉方括号
set "merged=%merged:[=%"
set "merged=%merged:]=%"

:: 清空输出文件
break > "%output%"

:: ===========================================
:: 第二步：每三个数字为一行输出
:: ===========================================
set /a count=0
set "line="
for %%n in (%merged%) do (
    set /a count+=1
    if !count! EQU 1 (
        set "line=%%n"
    ) else (
        set "line=!line! %%n"
    )
    if !count! EQU 3 (
        >>"%output%" echo !line!
        set "count=0"
        set "line="
    )
)

:: 去掉文件末尾空行（利用 findstr 过滤）
findstr /r /v "^$" "%output%" > "%output%.tmp"
move /y "%output%.tmp" "%output%" >nul

echo 处理完成
echo 输出文件: %output%
pause
