# src\data\vir100_25\vir100_25.m2d
M2D_FILE="D:\AAA_PIC\Parser\MCL_PLYParser\src\data\TestCMD\TM03_BWO.m2d"
TXT_FILE="D:\AAA_PIC\Parser\MCL_PLYParser\src\data\TestCMD\workdir\TM03_BWO.txt"
JSON_FILE="D:\AAA_PIC\Parser\MCL_PLYParser\src\data\TestCMD\workdir\commands.json"


start_time=$(date '+%Y-%m-%d %H:%M:%S.%3N')

#python src/mcl_preprocess.py "$M2D_FILE" -o "$TXT_FILE"

parser_time=$(date '+%Y-%m-%d %H:%M:%S.%3N')

#python src/parser/mcl_parser.py "$TXT_FILE" -o "$JSON_FILE"

conv_time=$(date '+%Y-%m-%d %H:%M:%S.%3N')

python src/conv/mcl_conv.py "$JSON_FILE"

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