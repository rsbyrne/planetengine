import os
def collect_by_keys(reader, paramKey, metricKey):
    paramDict, metricDict = reader[paramKey, metricKey]
    outDict = dict()
    for key, val in paramDict.items():
        try: outDict[val] = metricDict[key]
        except KeyError: pass
    return outDict
