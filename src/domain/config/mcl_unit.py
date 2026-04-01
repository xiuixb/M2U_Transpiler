"""
==========================
src/domain/config/mcl_unit.py
==========================
定义了转译过程中需要的一些规则，包括：
- 预处理物理量单位识别规则
"""

class MCLUNIT:
    BASE_UNITS = {
        # Physical constants
        "sec","second","c","rad","radian","pi","deg","degree",

        # Length
        "mil","mils","inch","foot","feet","micron","mm","cm","m","meter","km",

        # Frequency
        "hertz","hz","khz","mhz","ghz","thz",

        # Electromagnetic
        "a","amp","volt","kv","tesla","gauss","ohm","mho",
        "henry","farad","coulomb","v","t","h","f",

        # Energy
        "ev","kev","mev","gev","joule","watt",
    }

    # --------------------------
    # 前缀集合（全部小写）
    # --------------------------
    PREFIXES = {
        "atto","femto","pico","nano","micro",
        "milli","centi","deci",
        "kilo","mega","giga","tera","peta","exa",""
    }

    # --------------------------
    # auto-generate prefixed units
    # --------------------------
    FULL_UNITS = set(BASE_UNITS)

    for prefix in PREFIXES:
        for base in BASE_UNITS:
            FULL_UNITS.add(prefix + base)

    # remove ambiguous combinations：
    # e.g. kilokv, megav, gigapi → 如果需要可加限制
    # 暂时保留，匹配时不会伤害逻辑

    # 最终白名单
    VALID_UNITS = sorted(FULL_UNITS)

mcl_units = MCLUNIT.VALID_UNITS


