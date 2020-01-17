import everest
import weakref

class Observer(everest.built.Built):

    def __init__(
            self,
            inputs,
            script,
            system,
            outDict
            ):

        outDict['modeltime'] = system.modeltime

        system.attach_observer(self)

        self.orders = lambda: False
        self.system = system
        self.outDict = outDict
        self.outkeys = [*sorted(self.outDict)]

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

    def set_orders(self, orders):
        self.orders = orders

    # def prompt(self):
    #     if self.orders():
    #         self.store()
    #         if len(self.stored) >
