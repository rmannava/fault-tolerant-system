""" Messages within the distributed system. """

class Message:

    def __init__(self, identifier=None, number=None, data=None, state=None,
                 encoded=None):
        self.valid = True
        if encoded is not None:
            decoded = encoded.decode('utf-8')
            if decoded == '':
                self.valid = False
                return
            parts = decoded.split('\n\n')
            self.identifier = parts[0]
            self.number = parts[1]
            self.data = parts[2]
            self.state = parts[3]
            if self.data == '':
                self.data = None
            if self.state == '':
                self.state = None
        else:
            self.identifier = identifier
            self.number = number
            self.data = data
            self.state = state


    def encode(self):
        if self.data is None:
            self.data = ''
        if self.state is None:
            self.state = ''
        combined = [str(self.identifier), str(self.number), str(self.data),
                    str(self.state)]
        return ('\n\n'.join(combined)).encode('utf-8')
