from typing import Dict, List, Union, Optional


class toInFileTxt:
    class XmlTag:
        def __init__(self, tag_type: str, tag_name: str):
            self.tag_type = tag_type
            self.tag_name = tag_name
            self.content = []  # 存储键值对、子标签或空行

        def add_key_values(self, data: Dict) -> 'toInFileTxt.XmlTag':
            """添加键值对内容，返回self支持链式调用"""
            for k, v in data.items():

                self.content.append(f"{k} = {self._format_value(v)}")
            return self

        def add_inner_xml(self, xml_tag: 'toInFileTxt.XmlTag') -> 'toInFileTxt.XmlTag':
            """添加嵌套的XML标签，返回self支持链式调用"""
            self.content.append(xml_tag)
            return self

        def add_empty_line(self) -> 'toInFileTxt.XmlTag':
            """添加空行，返回self支持链式调用"""
            self.content.append(None)
            return self

        def add_string(self, string: str) -> 'toInFileTxt.XmlTag':
            """添加字符串内容，返回self支持链式调用"""
            self.content.append(string)
            return self

        def _format_value(self, value: Union[str, int, float, List]) -> str:
            """值类型格式化"""
            if isinstance(value, list):
                return f"[{' '.join(map(self._format_value, value))} ]"
            elif isinstance(value, float):
                return str(round(value, 10))
            return str(value)

        def to_string(self, indent_level: int = 0, indent_width: int = 2) -> str:
            """
            生成完整的XML字符串
            :param indent_level: 当前缩进层级
            :param indent_width: 每级缩进空格数
            """
            indent = ' ' * indent_level * indent_width
            lines = [f"{indent}<{self.tag_type} {self.tag_name}>"]

            # 处理内容缩进
            content_indent = ' ' * (indent_level + 1) * indent_width
            for item in self.content:
                if item is None:  # 空行
                    lines.append("")
                elif isinstance(item, toInFileTxt.XmlTag):
                    # 递归处理嵌套标签
                    lines.append(item.to_string(indent_level + 1, indent_width))
                else:
                    lines.append(f"{content_indent}{item}")

            lines.append(f"{indent}</{self.tag_type}>")
            return '\n'.join(lines)

    @staticmethod
    def create_xml_tag(tag_type: str, tag_name: str) -> 'XmlTag':
        """创建XML标签对象"""
        return toInFileTxt.XmlTag(tag_type, tag_name)

    @staticmethod
    def json_to_key_value(data: Dict, keys: Optional[List[str]] = None) -> str:
        """将JSON转换为键值对字符串"""
        lines = []
        selected_keys = keys if keys else data.keys()
        for k in selected_keys:
            if k in data:
                value = data[k]
                formatted = round(value,10)
                lines.append(f"{k} = {formatted}")
        return '\n'.join(lines)


if __name__ == '__main__':
    # 链式调用创建复杂结构
    field_src = (toInFileTxt.create_xml_tag("FieldSrc", "MurVoltagePort")
    .add_key_values({
        "mask": 6,
        "fileName": "EdgeHardSrc_6.h5"
    })
    .add_key_values({
        "kind": "MurVoltagePort",
        "version": 1.0
    })
    .add_empty_line()
    .add_inner_xml(
        toInFileTxt.create_xml_tag("Function", "Vin")
        .add_key_values({
            "amp": 490000.0,
            "tFall": 3e-7
        })
        .add_key_values({
            "tRise": 2e-9,
            "tStart": 0.0
        })
    )
    )
    # 生成带空行的XML
    print("Chain-style construction result:")
    print(field_src.to_string(indent_width=2))