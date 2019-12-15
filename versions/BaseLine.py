import mosaik_api
import random

NORM_VOLTAGE = 230
BATTERY_CAPACITY = 40000

meta = {
    'versions': {
        'AlohaOben': {
            'public': True,
            'any_inputs': True,
            'params': ['node_id', 'id'],
            'attrs': ['node_id', 'voltage', 'Vm', 'Va', 'P_out', 'Q_out', 'arrival_time', 'departure_time',
                      'available', 'current_soc', 'possible_charge_rate', 'Q', 'P'],
        },
    }
}


class BaseLine:
    def __init__(self, node_id, id):
        self.data = node_id
        self.step_size = 60
        self.counter = 0
        self.node_id = node_id
        self.voltage = 230.0
        self.P_out = 0.0
        self.Q_out = 0.0
        self.Vm = 230.0
        self.id = id
        self.chargingFLAG = False
        self.newCharging = False
        self.waitingTime = 0
        self.chargingTime = 0
        self.VmOLD = 0
        self.P_old = 0.0

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

    def checkAtt(self, attr):
        if attr == -1:
            return False
        else:
            return True

    def calcPower(self, inputs):
        available = self.getAtt('available', inputs)
        if available:
            possible_charge_rate = self.getAtt('possible_charge_rate', inputs)
            Vm = self.getAtt('Vm', inputs)
            if self.checkAtt(possible_charge_rate) & self.checkAtt(Vm) & self.voltageHighEnough(Vm):
                # return possible_charge_rate * Vm
                return possible_charge_rate * Vm
        return 0.0

    def calculatePowerIndex(self, Vm):
        if self.voltageHighEnough(Vm):
            powerIndex = 20 * Vm / NORM_VOLTAGE - 17.6
            if (powerIndex >= 0.0) & (powerIndex <= 1.0):
                return powerIndex
            elif powerIndex > 1:
                return 1.0
        return 0

    def voltageHighEnough(self, Vm):
        if Vm > 230 * 0.93:
            return True
        else:
            return False

    def step(self, simTime, inputs):
        if self.getAtt('available', inputs) & (self.getAtt('current_soc', inputs) < 100.0):
            if (not self.chargingFLAG) & (self.waitingTime == 0):  # not charging right now, but waiting time is over
                self.newCharging = True
                self.charging(simTime, inputs)
            elif (not self.chargingFLAG) & (self.waitingTime > 0):  # not charging right now, waiting time not yet over
                self.waitingTime -= 1
            elif self.chargingFLAG:  # charging right now, time is not over
                self.charging(simTime, inputs)

    def charging(self, simTime, inputs):
        P = self.calcPower(inputs)
        if P > 0:
            self.P_out = P
            self.chargingFLAG = True
        else:
            self.chargingFLAG = False
            self.waitingTime = self.calculateWaitingTime(simTime, inputs)

    def calculateWaitingTime(self, simTime, inputs):
        departure = self.getAtt('departure_time', inputs)
        currentTime = simTime
        timeUntil = departure - currentTime

        current_soc = self.getAtt('current_soc', inputs)
        # amount of power needed
        if current_soc < 100:
            neededcharge = BATTERY_CAPACITY * (1 - (current_soc / 100))
            P = self.getAtt('possible_charge_rate', inputs) * self.getAtt('Vm', inputs)
            # in hours
            neededTimeHours = neededcharge / P
            # in Minutes
            neededTime = int(neededTimeHours * 60)
            upperBorder = timeUntil - neededTime
        else:
            return departure - currentTime

        random.seed(42)
        return random.randrange(0, max(int((upperBorder / 2)), 2), 1)
