class Crc8:
    CRC_POLYNOM = 0x8c  # 低位传输时标准多项式
    CRC_INITIAL = 0x00

    value = CRC_INITIAL  # 全局变量

    # 计算crcTable，即0~255对应的crc8值
    dividend = 0
    remainder = 0
    crcTable = []
    for i in range(1000):
        crcTable.append(0)
    while dividend < 256:
        remainder = dividend
        bit = 0
        while bit < 8:
            bit = bit + 1
            # 与标准多项式异或操作
            if (remainder & 0x01) != 0:
                remainder = (remainder >> 1) ^ CRC_POLYNOM
            # 如果最低位是0则向右移一位
            else:
                remainder = remainder >> 1
        crcTable[dividend] = remainder
        dividend = dividend + 1

    # 用于计算一串数据的crc8，例如：DatumData中的ssid_crc8
    # self.value是之前所有数据得到的crc8值
    # tep是此次输入的需要计算crc8的数字
    def update(self, tep):
        i = 0
        value = self.value
        while i < 1:
            i = i + 1
            # 当前数据与此次输入的数据取异的值作为本次用来计算crc8的数据:data
            data = tep ^ value
            # data与0xff和操作取到数据低8位的值，通过crcTable得到对应的crc8值:data_crc8
            # 当前数据左移8位然后与data_crc8异或得到新的数据，低8位为刚刚计算得到的data_crc8
            value1 = (self.crcTable[data & 0xff] ^ (value << 8))
            self.value = value1
