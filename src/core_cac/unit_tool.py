
from decimal import Decimal, ROUND_HALF_UP
from pint import UnitRegistry, Quantity

ureg = UnitRegistry()

class UnitTool:

    DEFAULT_UNIT_BY_DIM = {
        ureg.get_dimensionality("meter"): "mm",          # 长度 -> mm
        ureg.get_dimensionality("second"): "s",         # 时间 -> ms
        ureg.get_dimensionality("kilogram"): "g",        # 质量 -> g
        ureg.get_dimensionality("kelvin"): "degC",       # 温度 -> 摄氏（注意：温度涉及偏置单位）
        ureg.get_dimensionality("meter/second"): "m/s", # 速度 -> km/h（复合量纲也可以）
        ureg.get_dimensionality("volt"): "V", # 电压 -> V
    }

    @staticmethod
    def to_default_unit(q: Quantity) -> Quantity:
        dim = q.dimensionality
        target = UnitTool.DEFAULT_UNIT_BY_DIM.get(dim)
        if target is None:
            # 不在表里：你可以选择保持原单位，或转 base units
            return q
            # 或者：return q.to_base_units()
        return q.to(target)

    @staticmethod
    def to_default_num(var_num, var_unit: str):
        """
        输入:
            var_num: 数值 (int/float)
            var_unit: 单位字符串 (如 "cm", "mm", "km/h", "deg", "N", "psi")
        输出:
            (si_value, si_unit_str)
            其中 si_unit_str 为 SI 基本单位表达 (如 "meter", "kilogram / meter ** 3", "meter / second")
        """
        q = var_num * ureg(var_unit)          # 构造 Quantity
        q_si = UnitTool.to_default_unit(q)    # 转为 SI 基本单位（base units）

        return UnitTool.normalize_sig7_trim(q_si.magnitude), str(q_si.units)


    @staticmethod
    def normalize_sig7_trim(x: float, keep_after_first: int = 9):
        """
        规则：把 x 规范化为科学计数法 m*10^e (1<=|m|<10)，
            从 m 的整数位开始往后数，保留 1 + keep_after_first 位有效数字（默认 7 位），
            四舍五入(ROUND_HALF_UP)，然后去掉末尾无效 0。
        返回：
        - d_out: Decimal（十进制精确结果）
        - f_out: float（便于下游使用）
        - s_out: str（无科学计数法/或科学计数法的紧凑十进制串，便于打印）
        """
        # 0 直接返回
        if x == 0:
            return Decimal(0), 0.0, "0"

        d = Decimal(str(x))  # 关键：避免 float 二进制误差污染
        sign = -1 if d < 0 else 1
        d_abs = d.copy_abs()

        # 规范化到科学计数法：d_abs = m * 10^e，m in [1,10)
        # adjusted() = floor(log10(d_abs))
        e = d_abs.adjusted()
        m = d_abs.scaleb(-e)  # m = d_abs / 10^e

        # 要保留的有效位数：1 + keep_after_first（默认 7）
        sig = 1 + keep_after_first

        # 将 m 量化到 sig 位有效数字：
        # m in [1,10) => 量化到 (sig-1) 位小数
        quant = Decimal(1).scaleb(-(sig - 1))  # 10^-(sig-1)
        m_q = m.quantize(quant, rounding=ROUND_HALF_UP)

        # 处理量化后可能出现 m_q == 10（例如 9.9999999 -> 10.0000000）
        if m_q >= Decimal(10):
            m_q = m_q / Decimal(10)
            e += 1

        # 复原数值
        out = m_q.scaleb(e)
        if sign < 0:
            out = -out

        # 去掉末尾无效 0（以及可能的尾随小数点）
        out_n = out.normalize()

        # 转成紧凑字符串（避免出现指数形式时也能接受；若你强制不用指数我也可以再改）
        s_out = format(out_n, "f")

        # format(...,"f") 对极小/极大数会展开很多位，这里做个更务实的处理：
        # 若展开过长，则用科学计数法紧凑输出
        if len(s_out) > 40:
            s_out = format(out_n, "g")

        return UnitTool.format_small_scientific(out_n)

    @staticmethod
    def format_small_scientific(x, threshold=Decimal("1e-3"), sig=6) -> str:
        """
        |x| < threshold (且非0) -> 科学计数法（保留 sig 位有效数字）
        否则 -> 普通定点表示（不使用科学计数法）
        输入支持：int/float/Decimal
        """
        # 转 Decimal：float 用 str 规避二进制尾差
        if isinstance(x, Decimal):
            d = x
        elif isinstance(x, (int,)):
            d = Decimal(x)
        else:
            d = Decimal(str(x))

        if d == 0:
            return "0"

        ad = abs(d)

        # 小数用科学计数法
        if ad < threshold:
            # g：按有效数字输出；会自动用 e 形式
            return format(d, f".{sig}g")

        # 非小数：用定点表示，并去掉末尾无效 0
        s = format(d, "f")
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s
    
    @staticmethod
    def qty_mag_mm(q: Quantity, nd=10):
        """Quantity -> mm 数值"""
        return round(q.to(ureg.mm).magnitude, nd)


# 示例
if __name__ == "__main__":
    
    v, u = UnitTool.to_si(12.5, "cm")
    print(v, u)  # 0.125 meter

    v, u = UnitTool.to_si(90, "km/h")
    print(v, u)  # 25.0 meter / second

    v, u = UnitTool.to_si(1, "g/cm^3")
    print(v, u)  # 1000.0 kilogram / meter ** 3
