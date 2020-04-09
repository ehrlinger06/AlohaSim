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


class SlottedAloha_waitingTime_VDE_tau(SlottedAloha.SlottedAloha_Class):
    """
    This class implements a controller, which uses the VDE-controller in combination with the Aloha network protocol.
    This  class is also known as SA+T+F.
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
        self.latestCollisionTime = 0

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
            if (not self.chargingFLAG) & (self.waitingTime == 0):  # not charging right now, but waiting time is over
                self.charging(inputs)
            elif (not self.chargingFLAG) & (self.waitingTime > 0):  # not charging right now, waiting time not yet over
                # self.waitingTime -= 1
                self.whileWaiting()
            elif self.chargingFLAG and not self.stayConnected:  # charging right now, time is not over
                self.charging(inputs)
            elif self.chargingFLAG and self.stayConnected:
                self.chargingWhileWaiting(inputs)

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
            self.stayConnected = False
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

    def filterPowerValue(self, P_new):
        """
        uses a first oder-lag filter with the given parameter as an input.

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
            if self.stayConnected:
                self.waitingTime += 1
                self.chargingWhileWaiting(inputs)

    def calculateWaitingTime(self, inputs):
        """
        calculates a waiting time using vehicle parameters and the number of participants.
        When the first maximum possible waiting time is too small, smaller than 1, a second waiting time is calculated
        using a secondary method, with this secondary method comes the possibility to charge through the waiting time
        ignoring all possible collisions. This special treatment can not be received without a break, between two such
        times there has to be a period of normal charging or a waiting period.

        :param inputs: parameters received from other parts of the simulator
        """
        CollisionCounter.CollisionCounter.getInstance().waitingTimeCalculated(self.time)
        timeUntilDepature = self.getAtt('departure_time', inputs) - self.time
        remainingLoadingTime = self.calculateLoadingTime(inputs)
        # calculates first maximum possible waiting time
        sampleTime = int((timeUntilDepature - remainingLoadingTime) / self.participants)
        if sampleTime >= 1:
            # result is big enough for a standard treatment
            self.waitingTime = MyRandom.RandomNumber.getInstance().getRandomNumber(sampleTime + 1)
        elif sampleTime < 1:
            # reslut is too small, special treatment necessary
            upperLimit = (10 * (1 - (math.exp(sampleTime - 1)))) + 1
            self.waitingTime = MyRandom.RandomNumber.getInstance().getRandomNumber(max((min(upperLimit,
                                                                                            timeUntilDepature)) + 1, 1))
            # decides whether charging is allowed during waiting time
            if not self.stayedConnected:
                self.stayConnected = True
                self.stayedConnected = True
            else:
                self.stayConnected = False
                self.stayedConnected = False

    def chargingWhileWaiting(self, inputs):
        """
        similar to charging(), but in here all occurring collisions are ignored.

        :param inputs:  parameters received from other parts of the simulator
        """
        self.waitingTime -= 1
        self.chargingFLAG = True
        P_new = self.calcPower(inputs)
        self.P_out = self.filterPowerValue(P_new)
        if self.waitingTime == 0:
            self.stayConnected = False
            self.chargingFLAG = False

    def calculateLoadingTime(self, inputs):
        """
        calculates the remaining loading time using the norm voltage

        :param inputs: parameters received from other parts of the simulator
        :return: the needed charge time in minutes
        """
        neededCharge = BATTERY_CAPACITY * (1 - (self.getAtt('current_soc', inputs) / 100))
        return int((neededCharge / (NORM_VOLTAGE * CHARGE_SPEED)) * 60)

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
