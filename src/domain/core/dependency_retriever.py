import re
from typing import List, Dict, Set, Any, Tuple
from src.domain.config.cmd_dic import MCL2MID_CmdDict

class DependencyRetriever:
    """
    上下文依赖检索器
    用于检索MAGIC命令的依赖关系，构建LLM转换所需的上下文
    """

    def __init__(self):        
        # MAGIC的MCL命令的依赖关系
        self.mcl2mid_dict = MCL2MID_CmdDict()
        self.MCL_dependency_dict = self.mcl2mid_dict.MCL_dependency_dict
        
        # 存储已处理的命令，避免循环依赖
        self.processed_commands = set()
        
        # 中间符号表引用
        self.mid_symbols = None
        
        # 原始命令文本存储（用于递归查找）
        self.command_texts = {}

    def load_data(self, mcl_symbols, mid_symbols):
        """
        加载数据
        
        Args:
            mcl_symbols: 解析出来的MAGIC命令参数表
            mid_symbols: 中间符号表
            command_texts: 命令文本字典，格式为 {实例名: 原始命令文本}
        """
        self.mcl_symbols = mcl_symbols
        self.mid_symbols = mid_symbols

    def get_mcl_dependency_item(self, idx: int, cmd_type: str, command_text: str) -> List[str]:
        """
        获取命令的依赖项
        
        Args:
            cmd_type: 命令类型（MCL命令）
            command_text: 命令原始文本
            
        Returns:
            依赖文本列表
        """
        if not self.mcl_symbols:
            raise ValueError("请先调用 load_context 加载符号表")
            
        # 重置处理状态
        self.processed_commands.clear()
        
        return self._get_dependency_recursive(idx, cmd_type, command_text)

    def _get_dependency_recursive(self, now_idx: int, cmd_type: str, command_text: str, dependency_debug: bool = False) -> List[str]:
        """
        递归获取依赖项
        
        Args:
            cmd_type: 命令类型
            command_text: 命令文本
            visited: 已访问的实例名集合，用于避免循环依赖
            
        Returns:
            依赖文本列表
        """
        dependency_texts = []
        # print(f"[debug] mcl符号表: {self.mcl_symbols.cmds_list[81]}")


        cmd_type = cmd_type.split(" ")[0]
        if cmd_type not in self.MCL_dependency_dict:
            print(f"[warning] 未知命令类型: {cmd_type}")
            return dependency_texts
        
        command_list = command_text.split()
        # print(f"[debug] 命令列表: {command_list}")

        # 获取该命令类型的依赖语义类型列表
        dependency_types = self.MCL_dependency_dict[cmd_type]

        # print(f"[debug] 依赖语义类型: {dependency_types}")
        
        # 遍历每个依赖语义类型
        for idx, record in enumerate(self.mcl_symbols.cmds_list):
            if idx >= now_idx:
                continue
            #if record["command"] == "FUNCTION":
                # print(f"[debug] 函数FUNCTION:\n       {record}")
            cmd_type = record["command"]
            sys_name = record["payload"].get("sys_name", None)
            if sys_name is None:
                #print(f"[warning] {cmd_type} 类型未指定系统名称")
                continue
            else:
                if (sys_name in command_list) and cmd_type in dependency_types:
                    # 英文变量:间接的依赖:
                    indirect_dependency_items = record["payload"].get("dependency", [])
                    dependency_texts.extend(indirect_dependency_items)
                    if cmd_type not in ("ASSIGN",  "POINT", "LINE", "AREA"):
                        dependency_texts.append(
                            {
                                "sys_name": sys_name,
                                "command": cmd_type,
                                "text": record["text"]
                            }
                        )
        if dependency_debug:
            print(f"[debug] 命令的原文本: {command_text}")
            print(f"[debug] 找到的依赖项: {dependency_texts}")
        
        return dependency_texts

