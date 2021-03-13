import uuid

class Solver:
    guid = None

    def __init__(self):
        self.guid = uuid.uuid5()