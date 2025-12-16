@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ====== 配置路径 ======
set "src_dir=D:\AAA_PIC\Parser\MCL_PLYParser\src"
set "out_file=%src_dir%\all_code.txt"
set "gitignore_file=%src_dir%\.gitignore"

REM 清理旧输出
if exist "%out_file%" del "%out_file%"

echo [info] src_dir=%src_dir%

REM ===============================
REM 检查 src 下的 .gitignore
REM ===============================
if not exist "%gitignore_file%" (
  echo [error] src 下未找到 .gitignore，將采用“全量遍历”。
  goto :FALLBACK_SCAN
)

echo [info] 检测到 src\.gitignore，将按忽略规则过滤...

REM 读取 .gitignore 规则到变量（用分号分隔）
set "patterns="
for /f "usebackq delims=" %%p in ("%gitignore_file%") do (
  if not "%%p"=="" if not "%%p:~0,1%"=="#" (
    set "patterns=!patterns!;%%p"
  )
)

REM 遍历所有 py 文件并匹配忽略规则
for /r "%src_dir%" %%f in (*.py) do (
  set "skip="
  for %%p in (!patterns!) do (
    set "check=%%~f"
    REM 简单包含匹配：如果文件路径中包含忽略片段，则跳过
    if not "!check:%%p=!"=="!check!" set "skip=1"
  )
  if not defined skip (
    >> "%out_file%" echo ############  %%~nxf  ############
    type "%%f" >> "%out_file%"
    >> "%out_file%" echo.
    >> "%out_file%" echo.
  )
)

echo [done] 已根据 src\.gitignore 过滤并合并 Python 文件到 "%out_file%"
goto :END

REM ===============================
REM 回退方案：无 .gitignore
REM ===============================
:FALLBACK_SCAN
for /r "%src_dir%" %%f in (*.py) do (
  >> "%out_file%" echo ############  %%~nxf  ############
  type "%%f" >> "%out_file%"
  >> "%out_file%" echo.
  >> "%out_file%" echo.
)

echo [done] 已（不考虑 .gitignore）合并所有 Python 文件到 "%out_file%"
goto :END

:END
pause
