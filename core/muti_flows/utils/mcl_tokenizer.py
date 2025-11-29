
class Tokenizer:
    def __init__(self, string="", delimiter=None):
        """
        构造函数初始化字符串和分隔符。
        
        :param string: 要拆分的输入字符串
        :param delimiter: 用于拆分字符串的分隔符（默认是空格、制表符、换行符等）
        """
        self.set(string, delimiter)

    def set(self, string, delimiter=None):
        """
        设置新的字符串和分隔符。
        
        :param string: 要拆分的字符串
        :param delimiter: 用于拆分字符串的分隔符
        """
        self.buffer = string
        if delimiter is None:
            self.delimiter = " \t\n\r\f\v"  # 默认的分隔符（空格、制表符、换行符等）
        else:
            self.delimiter = delimiter
        self.currPos = 0  # 当前处理位置初始化为0
    
    def reset(self):
        """重置 currPos 为 0"""
        self.currPos = 0
    
    def set_string(self, string):
        """仅设置字符串，并复位当前位置"""
        self.buffer = string
        self.currPos = 0  # 复位当前位置

    def set_delimiter(self, delimiter):
        """仅设置分隔符，并复位当前位置"""
        self.delimiter = delimiter
        self.currPos = 0  # 复位当前位置
    
    def next(self):
        """
        返回下一个 token，直到结束。
        """
        if self.currPos >= len(self.buffer):
            return ""  # 如果已经没有字符可处理，返回空字符串

        token = ""  # 初始化当前 token
        self.skip_delimiter()  # 跳过分隔符

        # 追加字符到 token 直到遇到分隔符
        while self.currPos < len(self.buffer) and not self.is_delimiter(self.buffer[self.currPos]):
            token += self.buffer[self.currPos]
            self.currPos += 1
        return token

    def split(self):
        """
        返回一个字符串列表，其中每个元素是一个从当前 cursor 分割出的 token。
        """
        tokens = []
        while (token := self.next()) != "":  # 使用 Python 3.8+ 的 := 操作符
            tokens.append(token)
        return tokens

    def has_token(self, tk):
        """
        判断字符串中是否包含某个 token。
        
        :param tk: 要查找的 token
        :return: 如果包含返回 True，否则返回 False
        """
        tokens = self.split()
        return tk in tokens

    def skip_delimiter(self):
        """
        跳过前导的分隔符。
        """
        while self.currPos < len(self.buffer) and self.is_delimiter(self.buffer[self.currPos]):
            self.currPos += 1

    def is_delimiter(self, char):
        """
        判断给定的字符是否是分隔符。
        
        :param char: 要判断的字符
        :return: 如果是分隔符返回 True，否则返回 False
        """
        return char in self.delimiter


# 示例使用
if __name__ == "__main__":
    # 测试 Tokenizer
    tokenizer = Tokenizer("This is an example string with  space and \t tab", delimiter=" \t\n\r\f\v")
    print("Tokens:", tokenizer.split())
    print("Next token:", tokenizer.next())
    tokenizer.reset()
    print("Has 'example'? ", tokenizer.has_token("example"))
