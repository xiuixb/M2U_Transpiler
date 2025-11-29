
import os
import sys
import math

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

from pint import UnitRegistry
from pathlib import Path

from core.muti_flows.utils.get_geom_num import geo_counter

# 初始化单位注册表
ureg = UnitRegistry()

# 定义转换器常量类
class ConvConstants:
    def __init__(self,
                data_dir_name,
                emitter_type='',
                material_dir=None,
                axis_mcl_dir='X',
                axis_unipic_dir='Z'):
        
        self.PI = math.pi
        self.bool_Revo_vector = False
        self.geo_c = geo_counter()
        self.unit_lr = 1e-3 * ureg.meter

        # 可由外部参数决定
        self.data_dir = Path(project_root) / f"data/{data_dir_name}"
        self.pre_jsonl = self.data_dir / f"workdir/preprocessed.jsonl"
        self.parsed_json = self.data_dir / f"workdir/parsed_result.json"
        
        self.symbols_json = self.data_dir / 'workdir/symbols.json'
        self.result_in_dir = self.data_dir / 'Simulation'
        self.uni_symbols_json = self.data_dir / 'workdir/uni_symbols.json'
        self.mid_symbols_json = self.data_dir / 'workdir/mid_symbols.json'

        self.IF_Conv2Void = True
        self.axis_mcl_dir = axis_mcl_dir
        self.axis_unipic_dir = axis_unipic_dir
        self.ywaveResolutionRatio = 200
        self.zwaveResolutionRatio = 200

        self.positive_port_mask_num = -1
        self.open_port_mask_num = -1
        self.emitter_mask_num = []

        self.emitter_type = emitter_type
        self.material_dir = material_dir or r"D:\UNIPIC\Unipic2.5D_Training\UNIPIC20240819\bin\pic\MyRBWO\Material\material.xml"
        
        
        self.build_in_dir = self.result_in_dir / 'build.in'
        self.FaceBnd_in_dir = self.result_in_dir / 'FaceBnd.in'
        self.Species_in_dir = self.result_in_dir / 'Species.in'
        self.PtclSources_in = self.result_in_dir / 'PtclSources.in'
        self.StaticNodeFLds_in_dir = self.result_in_dir / 'StaticNodeFLds.in'
        self.FieldsDgn_in_dir = self.result_in_dir / 'FieldsDgn.in'
        self.PML_in_dir = self.result_in_dir / 'PML.in'
        self.CircuitModel_in_dir = self.result_in_dir / 'CircuitModel.in'
        self.GlobalSetting_in_dir = self.result_in_dir / 'GlobalSetting.in'

constants = None

def init_constants(*args, **kwargs):
    global constants
    constants = ConvConstants(*args, **kwargs)
    return constants




# 定义调试类
class AllDebug:
    def __init__(self):

        self.variable_debug = True
        self.function_debug = False
        self.str2qty_debug = False

        self.emit_debug = False
        self.area_debug = False
        self.port_debug = False

        self.conduct2void_debug = False

alldebug = AllDebug()