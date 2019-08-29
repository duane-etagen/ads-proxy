import sys
import socket
import asyncio
import logging
import ctypes

from . import structs, constants


logger = logging.getLogger(__name__)


class AdsProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        logger.debug('%s connected', self)
        self.peer_name = transport.get_extra_info('peername')
        self.transport = transport

    def connection_lost(self, transport):
        logger.debug('Disconnected %s (%s)', self, self.peer_name)

    def __repr__(self):
        return (f'<{self.__class__.__name__} peer_name={self.peer_name}>')

    def data_received(self, data):
        self.buffer += data
        if len(self.buffer) >= ctypes.sizeof(structs.AoEHeader):
            header = structs.AoEHeader.from_buffer(self.buffer)
            expected_bytes = header.tcp_header.length + ctypes.sizeof(structs.AmsTcpHeader)
            if len(self.buffer) >= expected_bytes:
                data = self.buffer[ctypes.sizeof(header):expected_bytes]
                self.buffer = self.buffer[expected_bytes:]
                self.ads_frame_received(header.target_net_id.address, header, data)


class ServerProtocol(AdsProtocol):
    def __init__(self, loop, plcs, net_id_to_host, masquerade_as):
        logger.debug('Server %s masquerading as %s', net_id_to_host, masquerade_as)
        self.loop = loop
        self.plcs = plcs
        self.transport = None
        self.peer_name = None
        self.buffer = bytearray()
        self.masquerade_as = structs.AmsNetId.from_string(masquerade_as)

    def plc_frame_received(self, plc, header, data):
        'PLC -> proxy -> client'
        logger.debug('Received from PLC: %r %r', plc, header)
        if header.target_net_id.address != self.masquerade_as.address:
            logger.warning('Received a frame from the PLC not destined for us? %s',
                           header.target_net_id.address)
            return

        if self.transport:
            self.transport.write(bytes(header) + data)

    def ads_frame_received(self, target_net_id, header, data):
        'ADS client -> proxy -> PLC'
        logger.debug('Received from client destined for %r: %r (buffer %d)',
                     target_net_id, header, len(self.buffer))
        orig_source = header.source_net_id.address
        header.source_net_id = self.masquerade_as
        logger.debug('Sending to %s header %s (source was: %s)', target_net_id,
                     header, orig_source)
        try:
            plc = self.plcs[target_net_id]
            plc.transport.write(bytes(header) + data)
        except Exception:
            logger.exception('PLC write failed')
        else:
            logger.debug('Wrote %d bytes to plc', ctypes.sizeof(header) + len(data))


class PlcClientProtocol(AdsProtocol):
    def __init__(self, server, plc_net_id, plc_host):
        logger.debug('PLC %s %s', plc_net_id, plc_host)
        self.server = server
        self.plc_net_id = plc_net_id
        self.plc_host = plc_host
        self.reader = None
        self.writer = None
        self.transport = None
        self.peer_name = None
        self.buffer = bytearray()

    def ads_frame_received(self, target_net_id, header, data):
        'PLC -> proxy -> client'
        self.server.plc_frame_received(self, header, data)


async def main(net_id_to_host, masquerade_as):
    loop = asyncio.get_running_loop()
    plcs = {}
    logger.debug('Starting the server...')

    # TODO we really only want one connection at a time
    server = ServerProtocol(loop, plcs, net_id_to_host, masquerade_as)

    server_coro = await loop.create_server(
        lambda: server,
        '127.0.0.1', constants.ADS_TCP_SERVER_PORT)

    logger.debug('Connecting to PLCs...')

    def create_connection(net_id, host):
        if ':' in host:
            host, port = host.split(':')
            port = int(port)
        else:
            port = constants.ADS_TCP_SERVER_PORT

        logger.debug('Connecting to %s:%d (%s)', host, port, net_id)
        proto = PlcClientProtocol(server, net_id, host)
        coro = loop.create_connection(lambda proto=proto: proto,
                                      host, port)
        loop.create_task(coro)
        return proto

    plcs.update(
        {net_id: create_connection(net_id, host)
         for net_id, host in net_id_to_host.items()}
    )

    logger.debug('Serving')
    async with server_coro:
        await server_coro.serve_forever()


def run(net_id_to_host, masquerade_as):
    try:
        asyncio.run(main(net_id_to_host, masquerade_as))
    except KeyboardInterrupt:
        pass
