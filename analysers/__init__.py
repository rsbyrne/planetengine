from everest.builts._callable import Callable

class Analyser(Callable):

    def __init__(self,
            **kwargs
            ):

        # Expects:
        # self._evaluate

        self.dataName = self.__class__.__name__
        key = self.inputs['key']
        if not key == self.defaultInps['key']:
            self.dataName += '_' + key

        super().__init__(**kwargs)

        # Callable attributes:
        self._pre_call_fns.append(self.pre_evaluate)
        self._call_fns.append(self.evaluate)
        self._post_call_fns.append(self.post_evaluate)

    def pre_evaluate(self):
        # to be overridden
        pass
    def evaluate(self):
        return self._evaluate()
    def post_evaluate(self):
        # to be overridden
        pass

    def __str__(self):
        return str(self())
