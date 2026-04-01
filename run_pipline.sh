#!/bin/bash

# 设置输入和输出文件路径

# data\BWO\BWO.m2d
M2D_FILE="D:\AAA_PIC\Parser\M2U_Transpiler\data\BWO\BWO.m2d"

# data\MILO_new\milo_new.m2d
M2D_FILE2="D:\AAA_PIC\Parser\M2U_Transpiler\data\MILO_new\milo_new.m2d"

# data\Mitl\Mitl.m2d
M2D_FILE3="D:\AAA_PIC\Parser\M2U_Transpiler\data\Mitl\Mitl.m2d"

# data\TM03_60GHz_Double\TM03_60GHz_Double.m2d    OBSERVE_EMITTED未处理
M2D_FILE4="D:\AAA_PIC\Parser\M2U_Transpiler\data\TM03_60GHz_Double\TM03_60GHz_Double.m2d"

# data\vir100_25\vir100_25.m2d
M2D_FILE5="D:\AAA_PIC\Parser\M2U_Transpiler\data\vir100_25\vir100_25.m2d"

# data\XCT_PB\XCT_PB_3.m2d         有很多弧形和真空区域，还没加东西
M2D_FILE6="D:\AAA_PIC\Parser\M2U_Transpiler\data\XCT_PB\XCT_PB_3.m2d"

start_time=$(date '+%Y-%m-%d %H:%M:%S.%3N')

python src/application/magic2unipic.py -I "$M2D_FILE"

end_time=$(date '+%Y-%m-%d %H:%M:%S.%3N')


echo "================================="
echo "开始时间: $start_time"
echo "解析时间: $parser_time"
echo "转换时间: $conv_time"
echo "结束时间: $end_time"
echo "================================="


echo "输入文件为: $M2D_FILE"
echo "预处理完成，TXT文件位于: $TXT_FILE"
echo "解析完成，JSON文件位于: $JSON_FILE"