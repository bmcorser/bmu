import json
import tempfile
from flask import Flask, request
from plumbum import cli
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

CURRENT = 0

@app.route('/awake')
def awake():
    return 'Yes!'

class ServeN(cli.Application):
    'Serve a number of requests then harikiri'
    _port = 9000
    _n = 0

    @cli.switch(['-p', '--port'], int)
    def server_port(self, port):
        self._port = port

    @cli.switch(['-n', '--requests'], int)
    def requests(self, n):
        self._n = n

    def main(self):
        file_list = [
            tempfile.NamedTemporaryFile(delete=False) for n in range(self._n)
        ]

        @app.route('/', defaults={'path': ''}, methods=['POST'])
        @app.route('/<path:path>', methods=['POST'])
        def dump_data(path):
            global CURRENT
            try:
                current_file = file_list[CURRENT]
            except IndexError:
                if self._n == 0:
                    current_file = tempfile.NamedTemporaryFile(delete=False)
                    file_list.append(current_file)
            current_file.write(
                json.dumps({
                    'payload': request.get_json(),
                    'headers': dict(request.headers),
                    'path': path,
                })
            )
            current_file.flush()
            current_file.close()
            CURRENT += 1
            if CURRENT == (self._n):
                print(json.dumps([f.name for f in file_list]))
                request.environ.get('werkzeug.server.shutdown')()
            return 'Ok'

        app.run(port=self._port)

if __name__ == '__main__':
    ServeN.run()
