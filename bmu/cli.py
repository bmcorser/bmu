from plumbum import cli
from . import config


class Cli(cli.Application):
    _port = 9000
    _conf_path = 'conf.yaml'

    @cli.switch(['-p', '--port'], int)
    def server_port(self, port):
        self._port = port

    @cli.switch(['-c', '--conf'], str)
    def conf_path(self, conf_path):
        self._conf_path = conf_path

    def main(self):
        config.populate(self._conf_path)
        from . import server  # make sure configurtion is all done
        server.main(self._port)
