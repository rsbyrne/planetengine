from everest.builts import Built

class Observer(Built):

    genus = 'observer'

    def __init__(
            self,
            inputs,
            script,
            system,
            outDict
            ):

        outDict['modeltime'] = system.modeltime

        system.attach_observer(self)

        self.system = system
        self.outDict = outDict
        self.outkeys = [*sorted(self.outDict)]
        self.orders = set()

        self.inputs = inputs
        self.script = script

        super().__init__()

    def update(self):
        self.count.value = self.system.count()

    def out(self):
        outs = []
        for key in self.outkeys:
            outs.append(self.outDict[key].evaluate())
        return outs

    def prompt(self):
        self.update()
        if any(self.orders):
            self.store()
