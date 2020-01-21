from everest.built import Built

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

        super().__init__(
            inputs = inputs,
            script = script
            )

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
