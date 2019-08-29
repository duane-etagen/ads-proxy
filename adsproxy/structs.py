import ctypes


class AmsNetId(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("octet", ctypes.c_ubyte * 6)]

    def __repr__(self):
        return self.address

    @property
    def address(self):
        return '.'.join(str(octet) for octet in self.octet)

    @classmethod
    def from_string(self, net_id):
        octets = [int(octet) for octet in net_id.split('.')]
        if len(octets) != 6:
            raise ValueError('Expected 6 octets')

        return AmsNetId((ctypes.c_ubyte * 6)(*octets))


class AmsTcpHeader(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('reserved', ctypes.c_uint16),
        ('length', ctypes.c_uint32),
    ]

    def __repr__(self):
        return (
            f'<{self.__class__.__name__} '
            f'length={self.length}>'
        )


class AoEHeader(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ('tcp_header', AmsTcpHeader),
        ('target_net_id', AmsNetId),
        ('target_port', ctypes.c_uint16),
        ('source_net_id', AmsNetId),
        ('source_port', ctypes.c_uint16),
        ('cmd_id', ctypes.c_uint16),
        ('state_flags', ctypes.c_uint16),
        ('length', ctypes.c_uint32),
        ('error_code', ctypes.c_uint32),
        ('invoke_id', ctypes.c_uint32),
    ]

    def __repr__(self):
        return (
            f'<{self.__class__.__name__} '
            f'tcp_header={self.tcp_header} '
            f'{self.source_net_id}:{self.source_port} -> '
            f'{self.target_net_id}:{self.target_port} '
            f'cmd_id={self.cmd_id!r} state_flags={self.state_flags!r} '
            f'length={self.length!r} error_code={self.error_code!r} '
            f'invoke_id={self.invoke_id!r}>'
        )
