from versions_unused.SA_preWaitingArrivers import SlottedAloha_preWaitingArrivers
import CollisionCounter as CollisionCounter
import LowVoltageCounter as LowVoltageCounter

import math

NORM_VOLTAGE = 230
TRAFO_LIMIT = 121000


class TauVde_Trafo(SlottedAloha_preWaitingArrivers):
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
        self.collisionCounter = 0
        self.Vm_10M_average = 230.0
        self.Vm_sum = 0

    def step(self, simTime, inputs, participants):
        self.participants = participants
        self.time = ((simTime - self.step_size) / self.step_size)

        P_from = self.getAtt('P_from', inputs)
        Q_from = self.getAtt('Q_from', inputs)

        self.S = math.sqrt(math.pow(P_from, 2) + math.pow(Q_from, 2))

        if self.getAtt('available', inputs) & (self.getAtt('current_soc', inputs) < 100.0):
            self.charging(inputs)

            if self.getAtt('Vm', inputs) <= (0.88 * NORM_VOLTAGE):
                CollisionCounter.CollisionCounter.getInstance().addCollisionVolt(self.time)
            if self.S >= TRAFO_LIMIT:
                CollisionCounter.CollisionCounter.getInstance().addCollisionTrafo(self.time)

            if (self.getAtt('Vm', inputs) <= (0.88 * NORM_VOLTAGE) or self.S >= TRAFO_LIMIT):
                CollisionCounter.CollisionCounter.getInstance().riseCounter()
        else:
            self.P_out = 0.0
            self.P_old = 0.0

        self.calc_10M_average(inputs)

    def charging(self, inputs):
        P_new = self.calcPower(inputs)

        if P_new > 0:
            self.P_out = self.filterPowerValue(P_new)
            self.chargingFLAG = True
        else:
            self.P_out = max(self.filterPowerValue(0.0), 1.0)
            if self.P_out == 1.0:
                self.P_out = 0.0
            self.chargingFLAG = False

    def calcPower(self, inputs):
        if self.getAtt('available', inputs):
            possible_charge_rate = self.getAtt('possible_charge_rate', inputs)
            Vm = self.getAtt('Vm', inputs)
            P = possible_charge_rate * Vm
            if not self.stayConnected:
                P = P * self.calculateVoltageIndex(Vm) * self.calculateTrafoIndex()
            return P
        return 0.0

    def calculateVoltageIndex(self, Vm):
        if self.voltageHighEnough(Vm):
            voltIndex = 20 * Vm / NORM_VOLTAGE - 17.6
            if (voltIndex >= 0.0) & (voltIndex <= 1.0):
                return voltIndex
            elif voltIndex > 1:
                return 1.0
        return 0

    def calculateTrafoIndex(self):
        if self.S <= TRAFO_LIMIT:
            trafoIndex = (-1 / 24200) * self.S + 5
            if (trafoIndex >= 0.0) & (trafoIndex <= 1.0):
                return trafoIndex
            elif trafoIndex > 1:
                return 1.0
        return 0.0

    def filterPowerValue(self, P_new):
        if self.P_old > P_new:
            difference = (self.P_old - P_new) * 0.632
            P_out = self.P_old - difference
            self.P_old = P_out
        else:
            difference = (P_new - self.P_old) * 0.632
            P_out = self.P_old + difference
            self.P_old = P_out
        return P_out

    def calc_10M_average(self, inputs):
        self.Vm_sum += self.getAtt('Vm', inputs)
        if self.time % 10 == 0:
            if self.time == 0:
                average = self.Vm_sum / 2
            else:
                average = self.Vm_sum / 10
            self.Vm_10M_average = average
            self.Vm_sum = 0.0