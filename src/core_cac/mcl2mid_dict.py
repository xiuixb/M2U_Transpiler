
class MCL2MID_Dict:
    def __init__(self):
        self.MCL_dependency_dict = {
            "ASSIGN": ["ASSIGN"],
            "FUNCTION": ["ASSIGN"],
            "POINT": ["ASSIGN"],
            "LINE": ["ASSIGN", "POINT"],
            "AREA": ["ASSIGN", "POINT"],
            "MARK": ["ASSIGN"],
            "CONDUCTOR": [],
            "PORT": ["FUNCTION", "LINE"],
            "EMISSION": [],
            "EMIT": ["EMISSION", "AREA"],
            "PRESET": ["FUNCTION"],
            "INDUCTOR": ["LINE"],
            "RESISTOR": ["LINE"],
            "FOIL": ["LINE","AREA"],
            "OBSERVE": ["POINT", "LINE"]
        }
        
        self.MID_dict = {
            "ASSIGN": ["variable"],
            "FUNCTION": ["function"],
            "POINT": ["point"],
            "LINE": ["line"],
            "AREA": ["area"],
            "MARK": ["mark"],
            "CONDUCTOR": ["material_assign"],
            "PORT": ["port", "field_excitation"],
            "EMISSION": ["emission_model"],
            "EMIT": ["emission_apply"],
            "PRESET": ["electromagnetic_field"],
            "INDUCTOR": ["inductor"],
            "RESISTOR": ["resistor"],
            "FOIL": ["foil_model"],
            "OBSERVE": ["diagnostic"]
        }

        self.MCL2MID_llmconv_List = {
            "MARK": [],
            "CONDUCTOR": [],
            "PORT": [],
            "EMISSION": [],
            "EMIT": [],
            "PRESET": [],
            "INDUCTOR": [],
            "RESISTOR": [],
            "FOIL": [],
            "OBSERVE": []
        }

        


        # 中间语义的依赖关系
        self.MID_dependency_dict = {
            # 基础命令
            "variable": ["variable"],  # 变量可能依赖其他变量
            "function": ["variable"],  # 函数可能依赖变量
            
            # 几何命令
            "point": ["variable"],  # 点可能依赖变量
            "line": ["variable", "point"],  # 线可能依赖变量和点
            "area": ["variable", "point"],  # 面可能依赖变量、点、线
            "geom_cac_result": ["area"],  # 几何区域计算结果可能依赖面
            "selection": ["point", "line", "area", "geom_cac_result"],  # 选择可能依赖点、线、面、几何计算结果
            
            # 材料命令
            "material_library": [],  # 材料库无依赖
            "material_assign": ["area", "material_library"],  # 材料应用依赖面、材料
            
            # 边界命令
            "port": ["selection"],  # 边界定义依赖几何选择
            
            # 物理实体命令
            "particle_library":[],
            "field_excitation": ["port", "function"],
            "emission_model": [],
            "emission_apply": ["selection"],

            "secondary_electron_emitter":[],
            "electromagnetic_field": ["function"],
            "inductor": ["selection"],
            "resistor": ["selection"],
            "foil_model": ["selection"],

            # 诊断命令
            "diagnostic": []
        }