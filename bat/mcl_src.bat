@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 设置源目录（根目录）
set "src_dir=D:\AAA_PIC\Parser\M2U_Transpiler"
REM 设置输出文件
set "out_file=%src_dir%\all_code\mcl_src_code.txt"

REM 如果存在旧文件则删除
if exist "%out_file%" del "%out_file%"

REM 按顺序拼接指定文件
for %%f in (
    "%src_dir%\src\core_symbol\muti_flows\mcl_preprocess.py"
    "%src_dir%\src\core_symbol\single_flows\mcl_lexer.py"
    "%src_dir%\src\core_symbol\single_flows\mcl_ast.py"
    "%src_dir%\src\core_symbol\single_flows\mcl_grammar.py"
    "%src_dir%\src\core_symbol\muti_flows\mclparser\mcl_ast_visit.py"
    "%src_dir%\src\core_symbol\muti_flows\mclparser\mcl_plyparser.py"
    "%src_dir%\src\core_symbol\muti_flows\mclparser\mcl_regex_parser.py"
    "%src_dir%\src\core_symbol\muti_flows\mclparser\parser_route.py"
    "%src_dir%\src\complex_cac\mcl_allparser.py"
    "%src_dir%\src\core_symbol\muti_flows\conv\geom_conv.py"
    "%src_dir%\src\core_symbol\muti_flows\conv\mcl2mid_sTconv.py"
    "%src_dir%\src\core_symbol\muti_flows\conv\mid_sTconv.py"
    "%src_dir%\src\core_symbol\muti_flows\conv\mid2uni_sTconv.py"
    "%src_dir%\src\core_symbol\muti_flows\conv\uni2inFiles.py"
    "%src_dir%\src\system\src.py"
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
