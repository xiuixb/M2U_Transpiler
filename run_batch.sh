#!/bin/bash

# 设置输入和输出文件路径

# data\BWO\BWO.m2d
M2D_FILE1="D:\AAA_PIC\Parser\M2U_Transpiler\data\BWO\BWO.m2d"

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


python src/controller/m2u_batch.py --input $M2D_FILE1 $M2D_FILE2 $M2D_FILE3 $M2D_FILE4 $M2D_FILE5
