""" Messages within the distributed system. """

class Message:

    def __init__(self, identifier=None, number=None, data=None, encoded=None):
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
        else:
            self.identifier = identifier
            self.number = number
            self.data = data


    def encode(self):
        combined = [str(self.identifier), str(self.number), str(self.data)]
        return ('\n\n'.join(combined)).encode('utf-8')
