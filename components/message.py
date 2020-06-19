""" Messages within the distributed system. """

class Message:

    def __init__(self, identifier=None, data=None, encoded=None):
        self.valid = True
        if encoded is not None:
            decoded = encoded.decode('utf-8')
            if decoded == '':
                self.valid = False
                return
            parts = decoded.split('\n\n')
            self.identifier = parts[0]
            self.data = parts[1]
        else:
            self.identifier = identifier
            self.data = data


    def encode(self):
        return (str(self.identifier) + '\n\n' + str(self.data)).encode('utf-8')
