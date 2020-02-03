import math

import mosaik_api
import random

NORM_VOLTAGE = 230
BATTERY_CAPACITY = 36253.11
CHARGE_SPEED = 96

meta = {
    'versions': {
        'AlohaOben': {
            'public': True,
            'any_inputs': True,
            'params': ['node_id', 'id', 'seed'],
            'attrs': ['node_id', 'voltage', 'Vm', 'Va', 'P_out', 'Q_out', 'arrival_time', 'departure_time',
                      'available', 'current_soc', 'possible_charge_rate', 'Q', 'P', 'P_from', 'Q_from', 'U_s'],
        },
    }
}

class TrafoLoad():
    def __init__(self, node_id, id, seed):
        self.data = node_id
        self.step_size = 60
        self.counter = 1
        self.node_id = node_id
        self.voltage = 230.0
        self.P_out = 0.0
        self.Q_out = 0.0
        self.Vm = 230.0
        self.id = id
        self.chargingFLAG = False
        self.arriverFlag = False
        self.waitingTime = 0
        self.chargingTime = 0
        self.VmOLD = 0
        self.P_old = 0.0
        self.P_new = 0.0
        self.arrivers = 0
        self.participants = 0
        self.seed = seed
        self.time = 0
        self.availableOld = False
        self.S = 0
        self.waitedTime = 0
        self.stayConnected = False
        self.S_old = 0

    def step(self, inputs):
        P_from = self.getAtt('P_from', inputs)
        Q_from = self.getAtt('Q_from', inputs)

        S = math.sqrt(math.pow(P_from, 2) + math.pow(Q_from, 2))
        self.S = max(S, self.S)
        print("aktuelle Last:", S)
        print("maximal Last bisher:", self.S)

    def getAtt(self, attr, inputDict):
        attrDict = inputDict.get(attr)
        if len(attrDict) == 1:
            attrList = list(attrDict.values())
            if len(attrList) == 1:
                return attrList[0]
            else:
                return -1
        else:
            return -1
