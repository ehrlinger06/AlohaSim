import CollisionCounter as CollisionCounter

import math

from versions.SA_preWaitingArrivers import SlottedAloha_preWaitingArrivers

NORM_VOLTAGE = 230
TRAFO_LIMIT = 121000


class TauVde_Trafo(SlottedAloha_preWaitingArrivers):
    """
    This class serves a baseline implementation, as it is not using any part of the Aloha network protocol.
    It just implements the VDE AR-N 4100 voltage controller with an additional transformer controller.
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
        self.S = 0
        self.waitedTime = 0
        self.stayConnected = False
        self.collisionCounter = 0
        self.Vm_10M_average = 230.0
        self.Vm_sum = 0

    def step(self, simTime, inputs, participants):
        """
        initiates all actions performed in one step

        :param simTime: current time in seconds
        :param inputs: c
        :param participants: number of active participants, which are able to charge or are charging
        """
        self.participants = participants
        self.time = ((simTime - self.step_size) / self.step_size)

        P_from = self.getAtt('P_from', inputs)
        Q_from = self.getAtt('Q_from', inputs)

        # calculate load on transformer
        self.S = math.sqrt(math.pow(P_from, 2) + math.pow(Q_from, 2))

        # decide whether a participant is able to receive power or not
        if self.getAtt('available', inputs) & (self.getAtt('current_soc', inputs) < 100.0):
            self.charging(inputs)

            # count different kinds of collisions independently
            if self.getAtt('Vm', inputs) <= (0.88 * NORM_VOLTAGE):
                CollisionCounter.CollisionCounter.getInstance().addCollisionVolt(self.time)
            if self.S >= TRAFO_LIMIT:
                CollisionCounter.CollisionCounter.getInstance().addCollisionTrafo(self.time)

            # count overall collisions
            if (self.getAtt('Vm', inputs) <= (0.88 * NORM_VOLTAGE) or self.S >= TRAFO_LIMIT):
                CollisionCounter.CollisionCounter.getInstance().riseCounter()
        else:
            self.P_out = 0.0
            self.P_old = 0.0

        self.calc_10M_average(inputs)

    def charging(self, inputs):
        """
        sets the amount of power a participant can charge with in this step

        :param inputs: parameters received from other parts of the simulator
        """
        P_new = self.calcPower(inputs)

        if P_new > 0:
            self.P_out = self.filterPowerValue(P_new, inputs)
            self.chargingFLAG = True
        else:
            self.P_out = max(self.filterPowerValue(0.0, inputs), 1.0)
            if self.P_out == 1.0:
                self.P_out = 0.0
            self.chargingFLAG = False

    def calcPower(self, inputs):
        """
        calculates the maximum amount of power a participant can charge in the current step

        :param inputs: parameters received from other parts of the simulator
        :return: the maximum amount of power a participant can charge in the current step
        """
        if self.getAtt('available', inputs):
            possible_charge_rate = self.getAtt('possible_charge_rate', inputs)
            Vm = self.getAtt('Vm', inputs)
            P = possible_charge_rate * Vm
            if not self.stayConnected:
                P = P * self.calculateVoltageIndex(Vm) * self.calculateTrafoIndex()
            return P
        return 0.0

    def calculateVoltageIndex(self, Vm):
        """
        calculates the index, that indicates which part of the possible amount of power is currently useable
        according to the VDE AR N 4100

        :param Vm: the current voltage
        :return: the calculated index
        """
        if self.voltageHighEnough(Vm):
            voltIndex = 20 * Vm / NORM_VOLTAGE - 17.6
            if (voltIndex >= 0.0) & (voltIndex <= 1.0):
                return voltIndex
            elif voltIndex > 1:
                return 1.0
        return 0

    def calculateTrafoIndex(self):
        """
        calculates the index, that indicates which part of the possible amount of power is currently useable
        according to the transformer load

        :return: the calculated index
        """
        if self.S <= TRAFO_LIMIT:
            trafoIndex = (-1 / 24200) * self.S + 5
            if (trafoIndex >= 0.0) & (trafoIndex <= 1.0):
                return trafoIndex
            elif trafoIndex > 1:
                return 1.0
        return 0.0

    def filterPowerValue(self, P_new, inputs):
        """
        uses a first oder-lag filter with the given parameter as an input

        :param P_new: the parameter before filtering
        :return: the filtered parameter
        """
        if self.P_old > P_new:
            if self.S > TRAFO_LIMIT and self.getAtt('Vm', inputs) > (NORM_VOLTAGE * 0.88):
                difference = (self.P_old - P_new) * 0.632
            else:
                difference = (self.P_old - P_new) * 0.632
            P_out = self.P_old - difference
            self.P_old = P_out
        else:
            difference = (P_new - self.P_old) * 0.632
            P_out = self.P_old + difference
            self.P_old = P_out
        return P_out

    def calc_10M_average(self, inputs):
        """
        calculate the average of the voltage levels of a 10 minute interval

        :param inputs: parameters received from other parts of the simulator
        """
        self.Vm_sum += self.getAtt('Vm', inputs)
        if self.time % 10 == 0:
            if self.time == 0:
                average = self.Vm_sum / 2
            else:
                average = self.Vm_sum / 10
            self.Vm_10M_average = average
            self.Vm_sum = 0.0