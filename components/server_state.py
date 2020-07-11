class ServerState:

    def __init__(self, state=None):
        self._sum = 0
        if state is not None:
            self._sum = int(state)


    def __str__(self):
        return str(self._sum)


    def update(self, value):
        self._sum += value
        return self._sum
