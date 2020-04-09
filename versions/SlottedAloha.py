import math

import mosaik_api
import random

NORM_VOLTAGE = 230
BATTERY_CAPACITY = 36253.11
CHARGE_SPEED = 96
TRAFO_LIMIT = 121000

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


class SlottedAloha_Class:
    """
    serves as a parent class for SA_participants_VDE_tau, SA_participants_VDE_tau_trafo, SA_waitingTime_VDE_tau
    and SA_waitingTime_VDE_tau_trafo
    """
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

    def step(self, simTime, inputs, participants):
        self.participants = participants
        self.time = ((simTime - self.step_size) / self.step_size)

        P_from = self.getAtt('P_from', inputs)
        Q_from = self.getAtt('Q_from', inputs)

        self.S = math.sqrt(math.pow(P_from, 2) + math.pow(Q_from, 2))
        if self.id == 0:
            print('S:', self.S, 'in step:', self.time, 'in controller Aloha_', self.id)

        if self.getAtt('available', inputs) & (self.getAtt('current_soc', inputs) < 100.0):
            if (not self.chargingFLAG) & (self.waitingTime == 0):  # not charging right now, but waiting time is over
                self.charging(inputs)
            elif (not self.chargingFLAG) & (self.waitingTime > 0):  # not charging right now, waiting time not yet over
                self.waitingTime -= 1
            elif self.chargingFLAG:  # charging right now, time is not over
                self.charging(inputs)
        else:
            self.chargingFLAG = False
            self.P_out = 0.0

    def charging(self, inputs):
        P = self.calcPower(inputs)
        # self.printing(inputs)

        if P > 0 and self.S <= TRAFO_LIMIT:
            print('   P:', P, 'in step:', self.time, 'in controller Aloha_', self.id)
            self.P_out = P
            self.chargingFLAG = True
            self.arriverFlag = False
        else:
            if P <= 0 and self.S <= TRAFO_LIMIT:
                print('   SlottedAloha_waitingTime: Vm COLLISION, S ok, in step:', self.time, 'in controller Aloha_',
                      self.id)
            elif P <= 0 and self.S > TRAFO_LIMIT:
                print('   SlottedAloha_waitingTime: Vm COLLISION, S COLLISION, in step:', self.time,
                      'in controller Aloha_', self.id)
            elif P > 0 and self.S > TRAFO_LIMIT:
                print('   SlottedAloha_waitingTime: Vm ok, S COLLISION, in step:', self.time,
                      'in controller Aloha_', self.id)
            self.P_out = 0.0
            self.chargingFLAG = False
            self.arriverFlag = False
            self.waitingTime = self.calculateWaitingTime(inputs)

    def calculateWaitingTime(self, inputs):
        random.seed(self.seed)
        return random.randrange(0, max(self.participants, 2), 1)

    def calculateLoadingTime(self, inputs):
        neededCharge = BATTERY_CAPACITY * (1 - (self.getAtt('current_soc', inputs) / 100))
        return int((neededCharge / (NORM_VOLTAGE * CHARGE_SPEED)) * 60)

    def printing(self, inputs):
        remainingLoadingTime = self.calculateLoadingTime(inputs)
        timeUntilDeparture = self.getAtt('departure_time', inputs) - self.time
        timeSinceArrival = self.time - self.getAtt('arrival_time', inputs)
        availableTime = self.getAtt('departure_time', inputs) - self.getAtt('arrival_time', inputs)
        id = 'Aloha_%s' % (self.id)
        timeUsed = max(timeSinceArrival, 1) / availableTime
        timeUseable = timeUntilDeparture / availableTime
        amountOfCharges = timeUntilDeparture / max(remainingLoadingTime, 1)
        formula = (amountOfCharges / math.pow(max(timeSinceArrival, 1), 2)) * (self.getAtt('current_soc', inputs) / 100)
        formula2 = amountOfCharges * (1 - (self.getAtt('current_soc', inputs) / 100))
        formula3 = (amountOfCharges / max(timeSinceArrival, 1)) / self.participants

        print('model: ', id, ', time: ', self.time)
        print('RESULTSTEP1: amountOfCharges: ', amountOfCharges)
        print('--timeUntilDeparture: ', timeUntilDeparture)
        print('--remainingLoadingTime: ', remainingLoadingTime)  # goes down, to 0, lower is better, max. 9 8,5
        print('current_soc: ', self.getAtt('current_soc', inputs))
        print('timeUsed: ', timeSinceArrival)  # goes up, from 0 to 1, lower is better
        print('RESULTSTEP2: amountOfCharges * timeSinceArrival:', amountOfCharges / max(timeSinceArrival, 1))
        print('participants: ', self.participants)  # not constant, goes up and down, lower is better
        print('RESULT: (amountOfCharges * timeUsed) / participants: ', formula3)
        # print('timeUntilDeparture: ', timeUntilDeparture)  # goes down, to 0, higher is better
        # print('timeSinceArrival: ', timeSinceArrival)  # goes up, from 0, lower is better
        # print('availableTime: ', availableTime)  # constant, higher is better
        # print('participants: ', self.participants)  # not constant, goes up and down, lower is better
        print('current_soc: ', self.getAtt('current_soc', inputs))  # goes up, to 100, higher is better
        # print('timeUsed: ', timeUsed)  # goes up, from 0 to 1, lower is better
        # print('timeUseable: ', timeUseable)  # goes down, from 1 to 0, higher is better

        # print('amountOfCharges: ', amountOfCharges)
        # print('formula: ', formula)
        # print('formula2: ', formula2)
        print("  ")
