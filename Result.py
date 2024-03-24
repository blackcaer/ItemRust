class Result:

    def __init__(self, data="", success=True, errors=[]):
        self.success = success
        self.data = data
        self.errors = errors
