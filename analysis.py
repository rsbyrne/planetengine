import numpy as np

from .utilities import message

class ArrayStripper:

    def __init__(self, arrayobj, indexer):
        # input should be a numpy array
        # and an appropriate tuple of indices
        # to index the target value.

        self.array = arrayobj
        self.indexer = indexer

    def evaluate(self):

        value = self.array.evaluate()
        for index in self.indexer:
            value = value[index]
        return value

class Analyser:

    def __init__(
            self,
            name,
            analyserDict,
            formatDict,
            step,
            modeltime,
            ):

        self.analyserDict = analyserDict
        self.formatDict = formatDict

        miscDict = {
            'step': step,
            'modeltime': modeltime
            }
        miscFormatDict = {
            'step': "{:.0f}",
            'modeltime': "{:.1E}",
            }
        self.analyserDict.update(miscDict)
        self.formatDict.update(miscFormatDict)

        self.keys = sorted(analyserDict, key=str.lower)
        self.header = ', '.join(self.keys)
        self.dataDict = {}
        self.data = [None] * len(self.keys)
        self.name = name
        self.dataBrief = "No data."

    def analyse(self):
        for key in self.keys:
            self.dataDict[key] = self.analyserDict[key].evaluate()
        self.data = [self.dataDict[key] for key in self.keys]
        self.dataBrief = [
            (key, self.formatDict[key].format(self.dataDict[key])) \
            for key in self.keys
            ]

    def report(self):
        self.analyse()
        for pair in self.dataBrief:
            message(pair[0], pair[1])

class DataCollector:

    def __init__(self, analysers):

        self.analysers = analysers
        self.headers = [analyser.header for analyser in self.analysers]
        self.names = [analyser.name for analyser in self.analysers]
        self.datasets = [[] for analyser in self.analysers]

    def collect(self):

        for index, analyser in enumerate(self.analysers):
            analyser.analyse()
            if not analyser.data in self.datasets[index]:
                self.datasets[index].append(analyser.data)

    def out(self):

        outdata = []
        for name, header, dataset in zip(self.names, self.headers, self.datasets):
            if len(dataset) > 0:
                dataArray = np.vstack(dataset)
            else:
                dataArray = None
            outdata.append((name, header, dataArray))
        return outdata

    def clear(self):
        self.datasets = [[] for analyser in self.analysers]
