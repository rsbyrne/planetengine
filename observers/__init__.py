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

        super().__init__(
            inputs = inputs,
            script = script
            )

    def out(self):
        self.count.value = self.system.count()
        outs = []
        for key in self.outkeys:
            outs.append(self.outDict[key].evaluate())
        return outs
