import math

import CollisionCounter as CollisionCounter
import RandomNumber as MyRandom
import versions.SlottedAloha as SlottedAloha

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


class SlottedAloha__participants_VDE_tau(SlottedAloha.SlottedAloha_Class):
    """
    This class implements a controller, which uses the VDE-controller in combination with the Aoloha network protocol.
    This  class is also known as SA+T.
    """
    def __init__(self, node_id, id, seed):
        self.data = node_id
        self.step_size = 60
        self.counter = 1
        self.node_id = node_id
        self.voltage = 230.0
        self.Vm = 230.0
        self.P_out = 0.0
        self.Q_out = 0.0
        self.id = id
        self.chargingFLAG = False
        self.waitingTime = 0
        self.P_old = 0.0
        self.P_new = 0.0
        self.participants = 0
        self.seed = seed
        self.time = 0
        self.S = 0
        self.stayConnected = False
        self.Vm_10M_average = 230.0
        self.Vm_sum = 0

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
                P = P * self.calculateVoltageIndex(Vm)
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

    def voltageHighEnough(self, Vm):
        """
        returns true, if the given voltage is high enough in comparison to the norm voltage or false otherwise

        :param Vm: the given voltage
        :return: a boolean
        """
        if Vm > 230 * 0.88:
            return True
        else:
            return False

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
            if self.waitingTime == 0:  # not charging right now, but waiting time is over
                self.charging(inputs)
            elif (not self.chargingFLAG) & (self.waitingTime > 0):  # not charging right now, waiting time not yet over
                # self.waitingTime -= 1
                self.whileWaiting()

            # count different kinds of collisions independently
            if self.getAtt('Vm', inputs) <= (0.88 * NORM_VOLTAGE):
                CollisionCounter.CollisionCounter.getInstance().addCollisionVolt(self.time)
            if self.S >= TRAFO_LIMIT:
                CollisionCounter.CollisionCounter.getInstance().addCollisionTrafo(self.time)

            # count overall collisions
            if (self.getAtt('Vm', inputs) <= (0.88 * NORM_VOLTAGE) or self.S >= TRAFO_LIMIT):
                CollisionCounter.CollisionCounter.getInstance().riseCounter()
        else:
            self.chargingFLAG = False
            self.P_out = 0.0
            self.P_old = 0.0
            self.waitingTime = 0

        self.calc_10M_average(inputs)

    def whileWaiting(self):
        """
        actions performend in every time step the controller is in a waiting period

        :param inputs: parameters received from other parts of the simulator
        """
        self.waitingTime -= 1
        self.P_out = max(self.filterPowerValue(0.0), 1.0)
        if self.P_out == 1.0:
            self.P_out = 0.0
        self.chargingFLAG = False
        self.arriverFlag = False

    def filterPowerValue(self, P_new):
        """
        uses a first oder-lag filter with the given parameter as an input

        :param P_new: the parameter before filtering
        :return: the filtered parameter
        """
        if self.P_old > P_new:
            difference = (self.P_old - P_new) * 0.632
            P_out = self.P_old - difference
            self.P_old = P_out
        else:
            difference = (P_new - self.P_old) * 0.632
            P_out = self.P_old + difference
            self.P_old = P_out
        return P_out

    def charging(self, inputs):
        """
        sets the amount of power a participant can charge with in this step

        :param inputs: parameters received from other parts of the simulator
        """
        P_new = self.calcPower(inputs)

        if P_new > 0:
            self.P_out = self.filterPowerValue(P_new)
            self.chargingFLAG = True
            self.arriverFlag = False
        else:
            self.P_out = self.filterPowerValue(0.0)
            self.chargingFLAG = False
            self.arriverFlag = False
            self.calculateWaitingTime(inputs)

    def calculateWaitingTime(self, inputs):
        """
        calculate a waiting time, using the number of participants

        :param inputs: parameters received from other parts of the simulator
        :return: a waiting time
        """
        CollisionCounter.CollisionCounter.getInstance().waitingTimeCalculated(self.time)
        self.waitingTime = MyRandom.RandomNumber.getInstance().getRandomNumber(self.participants, self.seed)

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