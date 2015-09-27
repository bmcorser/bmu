from plumbum import cli
from . import server


class Cli(cli.Application):
    _port = 9000

    @cli.switch(["-p"], int)
    def server_port(self, port):
        self._port = port

    def main(self):
        server.main(self._port)
