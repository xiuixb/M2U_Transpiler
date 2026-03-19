import os
import sys
import json

# 获取项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
while not os.path.exists(os.path.join(current_dir, ".project_mark")):
    parent_dir = os.path.dirname(current_dir)
    if    parent_dir != current_dir: current_dir = parent_dir
    else: raise FileNotFoundError("未找到项目根目录，检查.project_mark文件")
project_root = current_dir
sys.path.append(project_root)

from src.core_symbol.symbolBase import Unipic25dSymbolTable

import json
from pathlib import Path
from typing import Any, Dict, List, Union

class Uni2InFiles:
    """
    读取 uni_symbols.json，将各个逻辑 section 拆分写入 Simulation/*.in
    """

    # 顶层 key -> 输出文件名 的映射
    SECTION_FILE_MAP: Dict[str, str] = {
        "buildIn": "build.in",
        "FaceBndIn": "FaceBnd.in",
        "PtclSourcesIn": "PtclSources.in",
        "SpeciesIn": "Species.in",
        "PMLIn": "PML.in",
        "StaticNodeFLdsIn": "StaticNodeFLds.in",
        "CircuitModelIn": "CircuitModel.in",
        "GlobalSettingIn": "GlobalSetting.in",
        "FieldsDgnIn": "FieldsDgn.in",
    }

    def load_data(self, uni_symbols: Unipic25dSymbolTable, out_dir: Path):
        self.uni = uni_symbols
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------
    # 主入口：写出所有 section
    # ------------------------------------------------------------
    def write_all(self):
        """
        逐个 section 写入 Simulation/<file>.in
        规则：若该 section 项为空列表或 None，则不生成对应文件。
        """
        for section, fname in self.SECTION_FILE_MAP.items():
            items = getattr(self.uni, section, None)

            # 新增规则：空列表也跳过
            if not items:   # items 为 None 或 [] 时为 False
                print(f"[Uni2InFiles] skip {fname} (empty)")
                continue

            file_path = self.out_dir / fname
            text = self._render_section(section, items)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"[Uni2InFiles] write {fname}")


    # ------------------------------------------------------------
    # 渲染整个 section 成文本
    # ------------------------------------------------------------
    def _render_section(self, section: str, items: List[Dict[str, Any]]) -> str:
        lines = []
        #lines.append(f"########## {section} ##########")

        for idx, obj in enumerate(items):
            block = self._render_item(obj, indent=0)
            if block:
                lines.extend(block)
                if idx != len(items) - 1:
                    lines.append("")  # 分段空行

        return "\n".join(lines).rstrip() + "\n"

    # ------------------------------------------------------------
    # 根据 sys_type 分派 ini/xml 渲染
    # ------------------------------------------------------------
    def _render_item(self, obj: Dict[str, Any], indent: int) -> List[str]:
        t = obj.get("sys_type")
        if t == "ini":
            return self._render_ini(obj, indent)
        elif t == "xml":
            return self._render_xml(obj, indent)
        else:
            raise ValueError(f"Unknown sys_type: {t}")

    # ------------------------------------------------------------
    # INI 渲染：key = value
    # ------------------------------------------------------------
    def _render_ini(self, obj: Dict[str, Any], indent: int) -> List[str]:
        pad = " " * indent * 2
        out = []
        for k, v in obj.items():
            if k == "sys_type":
                continue
            out.append(f"{pad}{k} = {v}")
        return out

    # ------------------------------------------------------------
    # XML 渲染：支持 content 一维 + 二维数组
    # ------------------------------------------------------------
    def _render_xml(self, obj: Dict[str, Any], indent: int) -> List[str]:
        pad = " " * indent * 2
        xml_type = obj["xml_type"]
        xml_name = obj["xml_name"]

        lines = [f"{pad}<{xml_type} {xml_name}>"]

        content = obj.get("content", [])

        if content:
            # ------------------------------
            # 情况 1：二维数组（多个 builder 组）
            # ------------------------------
            if isinstance(content, list) and content and isinstance(content[0], list):
                for gi, group in enumerate(content):
                    prev_is_xml = False
                    for si, sub in enumerate(group):
                        is_xml = (sub.get("sys_type") == "xml")

                        # XML→XML 插空行
                        if si > 0 and prev_is_xml and is_xml:
                            lines.append("")

                        child_lines = self._render_item(sub, indent + 1)
                        lines.extend(child_lines)
                        prev_is_xml = is_xml

                    if gi != len(content) - 1:
                        lines.append("")  # 组之间空一行

            # ------------------------------
            # 情况 2：一维 content 列表
            # ------------------------------
            else:
                prev_is_xml = False
                for si, sub in enumerate(content):
                    is_xml = (sub.get("sys_type") == "xml")

                    # 相邻 XML → XML 插入空行
                    if si > 0 and prev_is_xml and is_xml:
                        lines.append("")

                    child_lines = self._render_item(sub, indent + 1)
                    lines.extend(child_lines)

                    prev_is_xml = is_xml

        lines.append(f"{pad}</{xml_type}>")
        return lines