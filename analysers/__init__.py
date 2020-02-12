from everest.builts._callable import Callable

class Analyser(Built):

    def __init__(self,
            **kwargs
            ):

        # Expects:
        # self.evaluator

        super().__init__(**kwargs)

        # Callable attributes:
        self._pre_call_fns.append(self.pre_evaluate)
        self._call_fns.append(self.evaluate)
        self._post_call_fns.append(self.post_evaluate)

    def pre_evaluate(self):
        # to be overridden
        pass
    def evaluate(self):
        return self.evaluator.evaluate()
    def post_evaluate(self):
        # to be overridden
        pass
