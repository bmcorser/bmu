class BaseBuildbotEvent(object):
    def __init__(self, payload):
        self.payload = payload

    def __call__(self):
        raise NotImplementedError()


class BuildStarted(BaseBuildbotEvent):

    def __call__(self):
        properties = {k: v for k, v, s in self.payload['build']['properties']}
        print("Build started for {0}".format(properties['revision']))


class BuildFinished(BaseBuildbotEvent):
    def __call__(self):
        properties = {k: v for k, v, s in self.payload['build']['properties']}
        if self.payload['build']['text'] == ['failed']:
            print("Build failed for {0}".format(properties['revision']))
        else:
            print("Build might have suceeded for {0}".format(properties['revision']))


handler = {
    'buildStarted': BuildStarted,
    'buildFinished': BuildFinished,
}
