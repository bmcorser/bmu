def BaseBuildbotEvent(object):
    def __init__(self, payload):
        self.payload = payload

    def __call__(self):
        print(self.payload)
        raise NotImplementedError()


def BuildStarted(BaseBuildbotEvent):
    pass


def BuildFinished(BaseBuildbotEvent):
    pass


handler = {
    'buildStarted': BuildStarted,
    'buildFinished': BuildFinished,
}
