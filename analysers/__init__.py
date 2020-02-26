from everest.builts._callable import Callable

class Analyser(Callable):

    @staticmethod
    def _process_inputs(inputs)
        if inputs['name'] is None:
            inputs['name'] = self.__class__.__name__ + '_' self.inputs['key']

    def __init__(self,
            **kwargs
            ):

        # Expects:
        # self._evaluate

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
