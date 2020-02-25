class LowVoltageCounter():
    __instance = None
    initialized = False
    voltageDict = {}
    tooLow = 0

    @staticmethod
    def getInstance():
        if LowVoltageCounter.__instance is None:
            LowVoltageCounter()
        return LowVoltageCounter.__instance

    def __init__(self):
        if LowVoltageCounter.__instance is not None:
            raise Exception("Singleton already present")
        else:
            LowVoltageCounter.__instance = self

    def addEntry(self, node_id, time, Vm, chargingFlag, stayConnected, P_out):
        LowVoltageCounter.tooLow += 1
        node_idDict = {
            "Vm": Vm,
            "chargingFlag": chargingFlag,
            "stayConnected": stayConnected,
            "P_out": P_out
        }
        if time in LowVoltageCounter.voltageDict:
            LowVoltageCounter.voltageDict[time][node_id] = node_idDict
        else:
            LowVoltageCounter.voltageDict[time] = {}
            LowVoltageCounter.voltageDict[time][node_id] = node_idDict

    def print(self):
        print("Results of LowVoltageCounter:")
        print("Amount of times under 207 V:", LowVoltageCounter.tooLow)
        for key in LowVoltageCounter.voltageDict.keys():
            print(key)
            for key, val in LowVoltageCounter.voltageDict[key].items():
                print(key, val)

