class IdGenerator:
    class __IdGenerator:
        def __init__(self, arg):
            self.val = arg
            self._id_counter = 0

        def __str__(self):
            return repr(self) + self.val

        def request_id(self):
            self._id_counter += 1
            return self._id_counter
    instance = None

    def __init__(self, arg):
        if not IdGenerator.instance:
            IdGenerator.instance = IdGenerator.__IdGenerator(arg)
        else:
            IdGenerator.instance.val = arg

    def __getattr__(self, name):
        return getattr(self.instance, name)
