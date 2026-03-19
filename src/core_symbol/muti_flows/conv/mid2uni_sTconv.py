import os
import sys
import traceback
import json

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

from pint import Quantity

from src.core_symbol.symbolBase import MagicSymbolTable, MidSymbolTable, Unipic25dSymbolTable
from src.core_symbol.muti_flows.utils.get_geom_num import geo_counter


class MID2UNI_STConv():
    def __init__(self,
                mid_symbols: MidSymbolTable,
                uni_symbols: Unipic25dSymbolTable,
                geo_c: geo_counter,
                ):
        self.mid_symbols = mid_symbols
        self.uni_symbols = uni_symbols

    def load_data(self, mid_symbols: MidSymbolTable):
        self.mid_symbols = mid_symbols

    def mid2uni_sTconv(self,
                       symbols_file: str,
                       unit_lr: Quantity,
                       axis_mcl_dir: str,
                       geo_c: geo_counter,
                       ywaveResolutionRatio: float,
                       zwaveResolutionRatio: float,
                       IF_Conv2Void: bool,
                       bool_Revo_vector: bool,
                       material_dir: str,
                       emitter_kind: str = "GaussEmitter"                       
                       ):
        ### 1. 保存变量表
        symbols = [
        {
            'name': name,
            'value': info['value'],
            'unit': info['unit']
        } for name, info in self.mid_symbols.symbol_table.items()
        ]
        os.makedirs(os.path.dirname(symbols_file), exist_ok=True)
        with open(symbols_file, 'w') as f:
            json.dump({'variables': symbols}, f, indent=2)
        
        ### 2. buildIn
        geo_c, port_num_dict, emit_num_list, positive_port_info = self.mid2buildIn(
            unit_lr = unit_lr,
            axis_mcl_dir = axis_mcl_dir,
            geo_c = geo_c,
            ywaveResolutionRatio = ywaveResolutionRatio,
            zwaveResolutionRatio = zwaveResolutionRatio,
            IF_Conv2Void= IF_Conv2Void,
            bool_Revo_vector = bool_Revo_vector,
        )

        ### 3. FaceBndIn
        self.mid2FaceBndIn(
                    port_num_dict = port_num_dict,
                    port_info = positive_port_info,                    
                    )
        
        ### 4. PtclSourcesIn
        self.mid2PtclSourcesIn(
            emit_num_list = emit_num_list,
            emitter_kind = emitter_kind
        )


        ### 5. PMLIn
        self.mid2PMLIn()


        ### 6. SpeciesIn
        self.mid2SpeciesIn()


        ### 7. FieldsDgn.in
        if self.mid_symbols.FieldsDgn:
            geo_c = self.mid2FieldsDgnIn(geo_c)

        ### 8. StaticNodeFLds.in
        rMax = self.GetrMax()
        if self.mid_symbols.presets is not None:
            self.mid2StaticNodeFLdsIn(rMax = rMax)

        
        ### 9. CircuitModel.in
        if self.mid_symbols.inductor is not None:
            # print(f"[info] {self.mid_symbols.inductor}")
            self.mid2CircuitModelIn()

        ### 10. FoilModel.in
        if self.mid_symbols.foilModel is not None:
            self.mid2FoilModelIn()

        ### 11. GlobalSetting.in
        self.mid2GlobalSettingIn(
            material_dir = material_dir,
        )

        return self.uni_symbols

       

    def mid2buildIn(self,
                    unit_lr: Quantity,
                    axis_mcl_dir: str,
                    geo_c: geo_counter,
                    ywaveResolutionRatio: float,
                    zwaveResolutionRatio: float,
                    IF_Conv2Void: bool = False,
                    bool_Revo_vector: bool = False,
                    ):
        
        print(f"[info] Saving buildIn")

        port_num_dict = {}
        emit_num_list = []
        positive_port_info = {}
        
        ## 1. 基础设置
        
        self.uni_symbols.buildIn.append({
            "sys_type": "ini",
            "unitScale": int( "{:.0e}".format(unit_lr.magnitude).split('e')[1] ),
            "backGround": "PEC",
            "geomAlgoTol": "1.0e-12"            
        })

        ## 2. GeomCtrl

        theGeomCtrl_list = []
        
        if IF_Conv2Void == True:
            # 如果是真空区域
            kind = "polygon"
            nameid = "polyBuilder"
            name = "voidarea"
            type_str = "polygon"
            material = "FREESPACE"
            pnt3D = []

            if (bool_Revo_vector == False):
                vectorBuilder = {
                        "sys_type":"xml",
                        "xml_type":"GeomBuilder",
                        "xml_name":"vectorBuilder",
                        "content":[{
                            "sys_type":"ini", "nameid": "vectorBuilder", "kind": "vector","name": "axis","type": "Dim","value": "[0.0 0.0 100.0]"
                        }]   
                    }
                theGeomCtrl_list.append(vectorBuilder)
                bool_Revo_vector = True


            for point in self.mid_symbols.void_area['pnts']:
                x, y = point
                if axis_mcl_dir == 'X':
                    pnt3D.extend(['0.0', str(y), str(x)])
                elif axis_mcl_dir == 'Y':
                    pnt3D.extend(['0.0', str(x), str(y)])
            # 用空格连接所有数字
            pnts = '[' + ' '.join(pnt3D) + ']'
            polygonbuilder = {
                "sys_type":"xml",
                "xml_type":"GeomBuilder",
                "xml_name":"polyBuilder",
                "content":[{
                    "sys_type":"ini", "kind": kind,"nameid": nameid,"name": name,"type": type_str,"material": material,"pnts": pnts
                }]   
            }
            theGeomCtrl_list.append(polygonbuilder)
            
            
            facebuilder = {
                    "sys_type":"xml",
                    "xml_type":"GeomBuilder",
                    "xml_name":"faceBuilder",
                    "content":[{
                        "sys_type":"ini", "nameid": "faceBuilder", "kind": "face","name": "polyFace","wireName": name,"isPlanar": 1
                    }]   
                }
            theGeomCtrl_list.append(facebuilder)


            revolution_mask_num = geo_c.get_mask_count()
            revolutionbuilder = {
                    "sys_type":"xml",
                    "xml_type":"GeomBuilder",
                    "xml_name":"revolutionBuilder",
                    "content":[{
                        "sys_type":"ini",
                        "nameid": "revolutionBuilder", "kind": "revolution","name": "revolModel","base": "polyFace",
                        "mask": revolution_mask_num, "vector":"axis", "material": material, "type": "oneWay", "angle": "360.0"
                    }]   
                }
            theGeomCtrl_list.append(revolutionbuilder)
            
            
            ###  portSelection
            theGeomCtrl_list, geo_c, port_num_dict, positive_port_info = self.mid2portSelection(
                theGeomCtrl_list,
                geo_c=geo_c,
            )
                            

            ### emitSelection
            theGeomCtrl_list, geo_c, emit_num_list = self.mid2emitSelection(
                theGeomCtrl_list,
                geo_c=geo_c,
            )

        theGeomCtrl = {
                "sys_type": "xml",
                "xml_name": "theGeomCtrl",
                "xml_type": "GeomCtrl",
                "content": [theGeomCtrl_list]
            }
        self.uni_symbols.buildIn.append(theGeomCtrl)

        ## 3. GridCtrl
        ### 基础设置
        theGridCtrl_list = [{
            "sys_type":"ini",
            "margin": 1, "waveLength": 1.0e-01, "axis": "z", "org": "[0.0000,0.0000,0.0000]", "rDir": "y"
        }]

        theGridCtrl_list = self.mid2GridDefine(
            theGridCtrl_list = theGridCtrl_list,
            ywaveResolutionRatio = ywaveResolutionRatio,
            zwaveResolutionRatio = zwaveResolutionRatio,
            axis_mcl_dir = axis_mcl_dir,
        )
        
        theGridCtrl = {
            "sys_type": "xml",                
            "xml_type": "GridCtrl",
            "xml_name": "theGC",
            "content": [theGridCtrl_list]
        }
        self.uni_symbols.buildIn.append(theGridCtrl)

        
        return geo_c, port_num_dict, emit_num_list, positive_port_info
        

    def mid2portSelection(self,
                      theGeomCtrl_list: list,    
                      geo_c: geo_counter,
                      ):
        
        port_num_dict = {}
        positive_port_info = None
        
        for port_name in self.mid_symbols.ports:
            port_info = self.mid_symbols.ports[port_name]
            if port_info['direction'] == 'POSITIVE':
                port_geom_value = port_info['geom_value']
                coord1, coord2 = port_geom_value
                midpoint = [(a + b) / 2 for a, b in zip(coord1, coord2)]
                refPnt = f"[{midpoint[0]} {midpoint[1]} {midpoint[2]}]"
                self.mid_symbols.result['inputMurPort_refPnt'] = refPnt
                
                positive_subFaceSelection_num = geo_c.get_subFaceSelection_count()
                positive_port_mask_num = geo_c.get_mask_count()
                port_num_dict["positive_subFaceSelection_num"] = positive_subFaceSelection_num
                port_num_dict["positive_port_mask_num"] = positive_port_mask_num
                
                materialType = "INPUTMURPORT"
                selection_builder = {
                    "sys_type":"xml",
                    "xml_type":"GeomBuilder",
                    "xml_name": "selectionBuilder"+ str(positive_subFaceSelection_num),
                    "content":[{
                        "sys_type":"ini",
                        "contextNodeName": "revolModel",
                        "kind": "subFaceSelection", "mask": positive_port_mask_num, "name": "selection" + str(positive_subFaceSelection_num),
                        "refPnt": refPnt, "materialType": materialType
                    }]
                }
                positive_port_info = port_info
                theGeomCtrl_list.append(selection_builder)
                
            
            elif port_info['direction'] == 'NEGATIVE':
                port_geom_value = port_info['geom_value']
                coord1, coord2 = port_geom_value
                midpoint = [(a + b) / 2 for a, b in zip(coord1, coord2)]
                refPnt = f"[{midpoint[0]} {midpoint[1]} {midpoint[2]}]"
                self.mid_symbols.result['openPort_refPnt'] = refPnt

                negative_subFaceSelection_num = geo_c.get_subFaceSelection_count()
                negative_port_mask_num = geo_c.get_mask_count()
                port_num_dict["negative_subFaceSelection_num"] = negative_subFaceSelection_num
                port_num_dict["negative_port_mask_num"] = negative_port_mask_num

                materialType = "OPENPORT"
                selection_builder = {
                    "sys_type":"xml",
                    "xml_type":"GeomBuilder",
                    "xml_name": "selectionBuilder"+ str(negative_subFaceSelection_num),
                    "content":[{
                        "sys_type":"ini",
                        "contextNodeName": "revolModel",
                        "kind": "subFaceSelection", "mask": negative_port_mask_num, "name": "selection" + str(negative_subFaceSelection_num),
                        "refPnt": refPnt, "materialType": materialType
                    }]
                }
                theGeomCtrl_list.append(selection_builder)
        
        return theGeomCtrl_list, geo_c, port_num_dict, positive_port_info
    
    def mid2emitSelection(self,
                        theGeomCtrl_list: list,
                        geo_c: geo_counter,                        
                        ):
        emit_num_list = []
        emit_kind = ""
        for emit in self.mid_symbols.emits:
            emit_type = emit['kind']
            if emit_type == 'emission':
                pass
            elif emit_type == 'emit':
                mobject = emit['mobject']
                if 'model' in emit:
                    emit_kind = emit['model']
                if 'ex_in' in emit:
                    ex_in = emit['ex_in']
                else:
                    ex_in = []
                refPnts = self.mid_symbols.result["emit_selection_refPnts"]

                """
                这里改为遍历refPnt中的所有点，逐个创建一个selection
                并将所有的selection对应的mask_num添加到emitter_mask_num中
                """
                for refPnt in refPnts:
                    # 创建selection
                    selection_num = geo_c.get_subFaceSelection_count()
                    emitter_mask_num = geo_c.get_mask_count()
                    emit_num_list.append(emitter_mask_num)

                    selection_builder = {
                        "sys_type":"xml",
                        "xml_type":"GeomBuilder",
                        "xml_name": "selectionBuilder"+ str(selection_num),
                        "content":[{
                            "sys_type":"ini",
                            "contextNodeName": "revolModel",
                            "kind": "subFaceSelection", "mask": emitter_mask_num, "name": "selection" + str(selection_num),
                            "refPnt": refPnt, "materialType": "EMITTER"
                        }]
                    }
                
                    theGeomCtrl_list.append(selection_builder)
                    # print("\n设置发射参考点完成...............\n", selection_builder.to_string(indent_width=2))
        #print("emit_kind = ", emit_kind)

        return theGeomCtrl_list, geo_c, emit_num_list
        
    def mid2GridDefine(self, 
                       theGridCtrl_list: list,
                       ywaveResolutionRatio: float,
                       zwaveResolutionRatio: float,
                       axis_mcl_dir: str,
                       ):
        lam = 1.0e-01
        y_ratio = ywaveResolutionRatio
        z_ratio = zwaveResolutionRatio

        # 按 Δ=最小尺寸 折算： ratio = λ / Δ
        # 注意：取整数至少为 1
        def to_ratio(cell_size_m):
            if cell_size_m is None or cell_size_m <= 0:
                return None
            return max(1, int(round(lam / cell_size_m)))
       
        if axis_mcl_dir == 'X':
            z_min = self.mid_symbols.grid.get('X1')
            y_min = self.mid_symbols.grid.get('X2')
        elif axis_mcl_dir == 'Y':
            # 如果以后支持 Y 为主轴，可按需要调整映射
            z_min = self.mid_symbols.grid.get('X2')
            y_min = self.mid_symbols.grid.get('X1')
        else:
            z_min = self.mid_symbols.grid.get('X1')
            y_min = self.mid_symbols.grid.get('X2')

        z_ratio_new = to_ratio(z_min)
        y_ratio_new = to_ratio(y_min)
        if z_ratio_new is not None:
            z_ratio = z_ratio_new
        if y_ratio_new is not None:
            y_ratio = y_ratio_new

        GridDefine1 = {
            "sys_type":"xml",
            "xml_type": "GridDefine",
            "xml_name": "gd1",
            "content":[{
                "sys_type":"ini",
                "dir": "y", "kind": "uniformGrid", "waveResolutionRatio": y_ratio
            }]
        }
        GridDefine2 = {
            "sys_type":"xml",
            "xml_type": "GridDefine",
            "xml_name": "gd2",
            "content":[{
                "sys_type":"ini",
                "dir": "z", "kind": "uniformGrid", "waveResolutionRatio": z_ratio
            }]
        }
        theGridCtrl_list.append(GridDefine1)
        theGridCtrl_list.append(GridDefine2)
        return theGridCtrl_list


    def mid2FaceBndIn(self,
                      port_num_dict: dict,
                      port_info: dict
                      ):
        print(f"[info] Saving FaceBndInIn")
        
        positive_port_mask_num = port_num_dict['positive_port_mask_num']
        FieldSrc_Function_kind = "tFunc"
        FieldSrc_Function_result = port_info['result']

        # 写入FieldSrc
        FieldSrc_para_dict = {
            "sys_type":"ini",
            "mask": positive_port_mask_num, "kind": "MurVoltagePort", "fileName": "Default.h5"
        }

        FieldSrc_Function_dict = {"sys_type":"ini"}        
        FieldSrc_Function_args = port_info['func_vars']
        for arg in FieldSrc_Function_args:
            FieldSrc_Function_dict.update(arg)
        FieldSrc_Function_dict.update({
            "kind": FieldSrc_Function_kind, "result": FieldSrc_Function_result
        })

        FieldSrc_Function = {
            "sys_type":"xml",
            "xml_type": "Function",
            "xml_name": "Vin",
            "content": [FieldSrc_Function_dict]
        }

        self.uni_symbols.FaceBndIn = [{
                "sys_type":"xml",                
                "xml_type": "FieldSrc",
                "xml_name": "MurVoltagePort",
                "content": [FieldSrc_para_dict, FieldSrc_Function]            
        }]

    
    def mid2PtclSourcesIn(self,                          
                          emit_num_list: list,
                          emitter_kind: str
                          ):
        print(f"[info] Saving PtclSourcesIn")
        
        emitter_mask_num = '['+ ' '.join([str(num) for num in emit_num_list]) + ']'

        Emitter = {
            "sys_type":"xml",
            "xml_type": "Emitter",
            "xml_name": "Emitter",
            "content" : [{
                "sys_type":"ini",
                "field_enhancement": 1.0, "threshold": "2.3e+07", "kind": emitter_kind, "outPtcl": "Species", "maskVector": emitter_mask_num, "applyTimes": "[0.0 1e-05]"
            }]
        }

        self.uni_symbols.PtclSourcesIn = [{
            "sys_type":"xml",
            "xml_type": "ParticleSource",
            "xml_name": "Emitter",
            "content" : [Emitter]
        }]

    def mid2PMLIn(self,
                  ):
        
        print(f"[info] Saving PMLIn")
        PMLIn = {
            "sys_type":"xml",
            "xml_type": "PML",
            "xml_name": "PMLSetting",
            "content" : [{
                "sys_type":"ini",
                "key": 1, "powerOrder": 3, "alpha": 0.0, "kappaMax": 40.0, "sigmaRatio": 7.5
            }]
        }
        self.uni_symbols.PMLIn = [PMLIn]

       
    def mid2SpeciesIn(self,
                      ):
        print(f"[info] Saving SpeciesIn")
        SpeciesIn = {
            "sys_type":"xml",
            "xml_type": "Species",
            "xml_name": "Species",
            "content" : [{
                "sys_type":"ini",
                "charge": "-1.6022e-19", "mass": "9.10938e-31", "ptclCreationRate": 3.0, "kind": "electron", "name": "Species"
            }]
        }
        self.uni_symbols.SpeciesIn = [SpeciesIn]

    def mid2FieldsDgnIn(self,
                        geo_c: geo_counter
                        ):
        print(f"[info] Saving FieldsDgnIn")

        for observe_entry in self.mid_symbols.FieldsDgn:
            FieldsDgn_content = {"sys_type":"ini"}

            observe_type = observe_entry['observe_type']
            if observe_type == "observe_field":
                observe_para_dic = {k: v for k, v in observe_entry.items() if k not in ['observe_type', 'field_kind']}
                observe_field_name = observe_para_dic["name"]
                method_name = f"get_{observe_field_name}_count"
                func = getattr(geo_c, method_name)()  # 反射调用方法
                observe_para_dic["name"] = observe_para_dic["name"] + str(func)
                
                FieldsDgn_content.update(observe_para_dic)
            
            elif observe_type == "observe_field_power" or observe_type == "observe_field_integral":
                observe_field_dic = {k: v for k, v in observe_entry.items() if k not in ['observe_type']}
                FieldsDgn_content.update(observe_field_dic)
            
            Dgn = {
                "sys_type":"xml",
                "xml_type": "FieldsDgn",
                "xml_name": "Dgn"+str(geo_c.get_Dgn_count()),
                "content" : [FieldsDgn_content]
            }
            self.uni_symbols.FieldsDgnIn.append(Dgn)

        return geo_c
    

    def GetrMax(self):
        """
        从void_area中读取pnts，通过比较找到point[0]的最大值作为rMax
        """
        # 获取几何点数据
        points = self.mid_symbols.void_area.get('pnts', [])
        
        # 初始化rMax为0
        rMax = 0.0
        
        # 遍历所有点，找到point[0]的最大值
        for point in points:
            if point[0] > rMax:
                rMax = point[0]
        
        rMax = round(rMax * 0.001, 3)
        # 将rMax值存储到all_cmds.results中，供其他函数使用
        self.mid_symbols.result['rMax'] = rMax
        return rMax


    def mid2StaticNodeFLdsIn(self, rMax: float):
        """
        从presets中读取StaticNodeFLdsIn
        """
        if not self.mid_symbols.presets: return
        print(f"[info] Saving StaticNodeFLdsIn")
        print(f"       rMax = {rMax}")
        
        StaticNodeFLd_para = {
            "sys_type":"ini",
            "axis": 2, "rDir": 1, "rMax": str(rMax), "kind": "ZRExpressionModel", "target": "mag", "startCenter": "[0.0 0.0 0.0]"
        }
        StaticNodeFLd_content_list = [StaticNodeFLd_para]

        for func_name, StaticNodeFLd in self.mid_symbols.presets.items():

            StaticNodeFLd_func_content = {
                "sys_type":"ini",
                "component":StaticNodeFLd["component"],
                "kind":StaticNodeFLd["kind"],                        
            }
            StaticNodeFLd_func_content.update(StaticNodeFLd["func_vars"])
            StaticNodeFLd_func_content.update({"result":StaticNodeFLd["result"]})

            StaticNodeFLd_func = {
                "sys_type": "xml",
                "xml_type": "Function",
                "xml_name": func_name,
                "content" : [StaticNodeFLd_func_content]
            }
            StaticNodeFLd_content_list.append(StaticNodeFLd_func)

        StaticNodeFLdIn = {
            "sys_type":"xml",
            "xml_type": "StaticNodeFLd",
            "xml_name": "ZRExpressionModel",
            "content" : StaticNodeFLd_content_list
        }
        self.uni_symbols.StaticNodeFLdsIn = [StaticNodeFLdIn]


    def mid2CircuitModelIn(self,
                           ):
        print(f"[info] Saving CircuitModelIn")
        inds = self.mid_symbols.inductor
        if not inds: return
        print(f"[info] Saving CircuitModelIn")

        # 逐个电感写一个 <CircuitModel ...> 块
        CircuitModelIn_list = []

        for i, inductor in enumerate(inds, start=1):
            tag_name = f"inductor{i}"
            CircuitModel_content_para = {
                "sys_type":"ini",
                "name": tag_name,
                "kind": inductor.get("kind", "Inductor"),
                "L": inductor.get("L", 0.0),
                "dir": inductor.get("dir", "r"),
                "lowerBounds": inductor["lowerBounds"],
                "upperBounds": inductor["upperBounds"],
            }

            CircuitModel = {
                "sys_type":"xml",
                "xml_type": "CircuitModel",
                "xml_name": f"inductor{i}",
                "content" : [CircuitModel_content_para]
            }

            CircuitModelIn_list.append(CircuitModel)
        
        self.uni_symbols.CircuitModelIn = CircuitModelIn_list

    def mid2FoilModelIn(self):
        pass

    def mid2GlobalSettingIn(self,
                            material_dir: str
                            ):
        print(f"[info] Saving GlobalSettingIn")

        runtime = self.mid_symbols.symbol_table.get("RUNTIME", {}).get("value")
        if runtime is None:
            runtime = self.mid_symbols.symbol_table.get("SIMULATION_TIME", {}).get("value")


        GlobalSettingIn = {
            "sys_type":"ini",
            "FilterMask": "0",
            "InterpolateType": "1",
            "emAdvanceOrder": "1",
            "ptclTrackNum": "1",
            "threadnum": "2",
            "CFLScale": "9.0e-01",
            "LangdonMarderDivParam": "0.0",
            "chiParam": "1.0",
            "emDamping": "1.0e-01",
            "parabolicDamping": "2.0e-01",
            "simulationTime": str(runtime),
            "EMSolver": "picMode",
            "dynEMkind": "SI_SC_PHM_Matrix",
            "emDumpSwitch": "ON",
            "jDumpSwitch": "ON",
            "materialLib": material_dir,
            "ptclDensityDumpSwitch": "OFF",
            "ptclDumpSwitch": "ON",
            "ptclTrackSwitch": "OFF",
            "rhoDumpSwitch": "OFF",
            "dumpStepVec": "[1.0e-09 ]",
            "dumpTimeNode": "[1.0e-05 ]",
            "ptclTrackProb": "[ ]",
            "ptclTrackTypes": "[ ]",
        }

        self.uni_symbols.GlobalSettingIn = [GlobalSettingIn]

        
