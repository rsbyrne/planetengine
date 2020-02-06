from everest.builts.producer import Producer

class Observer(Producer):

    genus = 'observer'

    def __init__(
            self,
            script,
            system,
            outDict
            ):

        outDict['chron'] = system.chron

        system.attach_observer(self)

        self.system = system
        self.outDict = outDict
        self.outkeys = [*sorted(self.outDict)]
        self.orders = set()

        super().__init__(self.out, self.outkeys)

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
