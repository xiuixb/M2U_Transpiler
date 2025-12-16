import os
import sys

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)


from pydantic import BaseModel
from typing import List, Tuple


class ProjectConfig(BaseModel):
    project_name: str

class GeometryConfig(BaseModel):
    points: List[Tuple[float, float, float]]
    shape_type: str           
    scale_factor: float | None

class GridCtrlConfig(BaseModel):
    dx: float
    dy: float
    dz: float
    time_step: float
    grid_type: str = "Yee"

class SelectionConfig(BaseModel):
    excitation_points: List[int]    # 几何点 index
    probe_points: List[int]
    port_ids: List[int]

class FaceBndConfig(BaseModel):
    face_id: int
    boundary_type: str   # PEC / PMC / PML / ABC / Port
    excitation_type: str | None
    amplitude: float | None
    phase: float | None

class PtclSourcesConfig(BaseModel):
    source_type: str           # emission / injected / cathode …
    position: Tuple[float, float, float]
    current_density: float
    temperature: float | None

class StaticNodeFLdsConfig(BaseModel):
    node_id: int
    field_type: str
    value: float

class CircuitModelConfig(BaseModel):
    inductance_L: float | None
    capacitance_C: float | None
    resistance_R: float | None
    enabled: bool = False

class FoilModelConfig(BaseModel):
    thickness: float
    conductivity: float
    enabled: bool = False

class FieldsDgnConfig(BaseModel):
    probe_positions: List[Tuple[float, float, float]]
    sample_rate: float
    record_fields: List[str]     # Ex, Ey, Ez, Bx, …
    fft_enabled: bool
    history_points: List[int]

class SpeciesConfig(BaseModel):
    name: str
    mass: float
    charge: float
    macro_particle_count: int
    initial_temperature: float

class PMLConfig(BaseModel):
    thickness: int
    conductivity_profile: str
    reflection_coeff: float

class GlobalSettingConfig(BaseModel):
    total_time: float
    output_interval: int
    solver_type: str      # FDTD, EM-PIC
    courant_factor: float

class ModelConfig(BaseModel):
    project_cfg: ProjectConfig
    geometry_cfg: GeometryConfig
    gridctrl_cfg: GridCtrlConfig
    selection_cfg: SelectionConfig
    facebnd_cfg: FaceBndConfig
    ptclsources_cfg: PtclSourcesConfig
    circuit_model_cfg: CircuitModelConfig
    foil_model_cfg: FoilModelConfig
    fieldsdgn_cfg: FieldsDgnConfig
    species_configs: SpeciesConfig
    pml_cfg: PMLConfig
    globalsetting_cfg: GlobalSettingConfig