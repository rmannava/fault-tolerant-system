class ServerState:

    def __init__(self):
        self._sum = 0

    def update(self, value):
        self._sum += value
        return self._sum
