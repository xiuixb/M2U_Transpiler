@echo off
setlocal enabledelayedexpansion

:: 设置根目录（根据需要修改）
set ROOT_DIR=src

:: 创建根目录
mkdir %ROOT_DIR%

:: 创建子目录和文件
cd %ROOT_DIR%

:: 创建lexer目录及文件
mkdir lexer
echo. > lexer\__init__.py
echo. > lexer\lexer.py
echo. > lexer\tokens.py

:: 创建parser目录及文件
mkdir parser
echo. > parser\__init__.py
echo. > parser\parser.py
echo. > parser\grammar.py
echo. > parser\ast.py

:: 创建semantic目录及文件（如果需要语义分析）
mkdir semantic
echo. > semantic\__init__.py
echo. > semantic\semantic_analysis.py
echo. > semantic\symbol_table.py

:: 创建generator目录及文件（如果需要代码生成）
mkdir generator
echo. > generator\__init__.py
echo. > generator\py_generator.py
echo. > generator\output.py

cd..

:: 创建utils目录及文件
mkdir utils
echo. > utils\__init__.py
echo. > utils\error_handling.py
echo. > utils\logger.py

:: 创建tests目录及文件
mkdir tests
echo. > tests\__init__.py
echo. > tests\test_lexer.py
echo. > tests\test_parser.py
echo. > tests\test_generator.py

:: 创建examples目录
mkdir examples
echo. > examples\example_script.mcl

:: 创建其他文件
echo. > README.md
echo. > requirements.txt
echo. > setup.py

:: 提示完成
echo 项目结构已创建完成！
pause
