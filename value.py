class Value:

    def __init__(self, val):
        self.value = val
        self.type = type(val)

    def __setattr__(self, item, value):
        if item in self.__dict__:
            if item == 'type':
                raise Exception("Forbidden to manually set 'type'.")
            elif item == 'value':
                if not type(value) == self.type:
                    raise Exception("New val is of different type to old val.")
                else:
                    dict.__setattr__(self, item, value)
            else:
                dict.__setattr__(self, item, value)
        else:
            dict.__setattr__(self, item, value)

    def __call__(self):
        return self.value
