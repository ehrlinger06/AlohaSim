import versions.SlottedAloha as SlottedAloha
import RandomNumber as MyRandom
import CollisionCounter as CollisionCounter
import LowVoltageCounter as LowVoltageCounter

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


class SlottedAloha_waitingTime_VDE_tau(SlottedAloha.SlottedAloha_Class):
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

    def calcPower(self, inputs):
        available = self.getAtt('available', inputs)
        if available:
            possible_charge_rate = self.getAtt('possible_charge_rate', inputs)
            Vm = self.getAtt('Vm', inputs)
            if self.checkAtt(possible_charge_rate) & self.checkAtt(Vm):
                self.P_new = possible_charge_rate * Vm * self.calculatePowerIndex(Vm)
                if self.P_old > self.P_new:
                    difference = (self.P_old - self.P_new) * 0.632
                    self.P_out = self.P_old - difference
                    self.P_old = self.P_out
                else:
                    difference = (self.P_new - self.P_old) * 0.632
                    self.P_out = self.P_old + difference
                    self.P_old = self.P_out
                return self.P_out
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
        if Vm > 230 * 0.88:
            return True
        else:
            return False

    def step(self, simTime, inputs, participants):
        self.participants = participants
        self.time = ((simTime - self.step_size) / self.step_size)

        P_from = self.getAtt('P_from', inputs)
        Q_from = self.getAtt('Q_from', inputs)

        self.S = math.sqrt(math.pow(P_from, 2) + math.pow(Q_from, 2))
        #if self.id == 0:
        #    print('S:', self.S, 'in step:', self.time, 'in controller Aloha_', self.id)

        if self.getAtt('available', inputs) & (self.getAtt('current_soc', inputs) < 100.0):
            if (not self.chargingFLAG) & (self.waitingTime == 0):  # not charging right now, but waiting time is over
                self.charging(inputs)
            elif (not self.chargingFLAG) & (self.waitingTime > 0):  # not charging right now, waiting time not yet over
                self.waitingTime -= 1
            elif self.chargingFLAG and not self.stayConnected:  # charging right now, time is not over
                self.charging(inputs)
            elif self.chargingFLAG and self.stayConnected:
                self.chargingWhileWaiting(inputs)
        else:
            self.chargingFLAG = False
            self.P_out = 0.0
            self.P_old = 0.0

        if self.getAtt('Vm', inputs) <= 207:
            LowVoltageCounter.LowVoltageCounter.getInstance().addEntry(self.node_id, self.time,
                                                                       self.getAtt('Vm', inputs), self.chargingFLAG,
                                                                       self.stayConnected, self.P_out)

        self.calc_10M_average(inputs)

    def charging(self, inputs):
        P = self.calcPower(inputs)
        # self.printing(inputs)

        if P > 0 and self.S <= TRAFO_LIMIT:
            #print('   P:', P, 'in step:', self.time, 'in controller Aloha_', self.id)
            self.P_out = P
            self.chargingFLAG = True
            self.arriverFlag = False
        else:
            #if P <= 0 and self.S <= 110000:
            #    print('   SlottedAloha_waitingTime: Vm COLLISION, S ok, in step:', self.time, 'in controller Aloha_', self.id)
            #elif P <= 0 and self.S > 110000:
            #    print('   SlottedAloha_waitingTime: Vm COLLISION, S COLLISION, in step:', self.time,
            #          'in controller Aloha_', self.id)
            #elif P > 0 and self.S > 110000:
            #    print('   SlottedAloha_waitingTime: Vm ok, S COLLISION, in step:', self.time,
            #          'in controller Aloha_', self.id)
            self.P_out = 0.0
            self.P_old = 0.0
            self.chargingFLAG = False
            self.arriverFlag = False
            self.calculateWaitingTime(inputs)
            if self.stayConnected:
                self.waitingTime += 1
                self.chargingWhileWaiting(inputs)

    def chargingWhileWaiting(self, inputs):
        self.waitingTime -= 1
        #print('   SlottedAloha_waitingTime: In step:', self.time, 'in controller Aloha_', self.id,
        #      'stayed connected, waitingTime until reentering normal charging:', self.waitingTime)
        self.chargingFLAG = True
        self.P_out = self.calcPower_VoltageNotHighEnough(inputs)
        if self.waitingTime == 0:
            self.stayConnected = False
            self.chargingFLAG = False

    def calculateWaitingTime(self, inputs):
        #self.collisionCounter += 1
        CollisionCounter.CollisionCounter.getInstance().addCollision(self.time)
        #print("collisionCounter: ", self.collisionCounter)
        timeUntilDepature = self.getAtt('departure_time', inputs) - self.time
        remainingLoadingTime = self.calculateLoadingTime(inputs)
        sampleTime = int((timeUntilDepature - remainingLoadingTime) / self.participants)
        if sampleTime >= 1:
            self.waitingTime = MyRandom.RandomNumber.getInstance().getRandomNumber(sampleTime)
        elif sampleTime < 1:
            upperLimit = (10 * (1 - (math.exp(sampleTime - 1)))) + 1
            self.waitingTime = MyRandom.RandomNumber.getInstance().getRandomNumber(max(min(upperLimit,
                                                                                           timeUntilDepature), 1))
            if not self.stayConnected:
                self.stayConnected = True
                self.stayedConnected = True
            else:
                self.stayConnected = False
                self.stayedConnected = False

    def calcPower_VoltageNotHighEnough(self, inputs):
        available = self.getAtt('available', inputs)
        if available:
            possible_charge_rate = self.getAtt('possible_charge_rate', inputs)
            Vm = self.getAtt('Vm', inputs)
            if self.checkAtt(possible_charge_rate) & self.checkAtt(Vm):
                self.P_new = possible_charge_rate * Vm
                if self.P_old > self.P_new:
                    difference = (self.P_old - self.P_new) * 0.632
                    self.P_out = self.P_old - difference
                    self.P_old = self.P_out
                else:
                    difference = (self.P_new - self.P_old) * 0.632
                    self.P_out = self.P_old + difference
                    self.P_old = self.P_out
                return self.P_out
        return 0.0

    def calc_10M_average(self, inputs):
        self.Vm_sum += self.getAtt('Vm', inputs)
        if self.time % 10 == 0:
            if self.time == 0:
                average = self.Vm_sum / 2
            else:
                average = self.Vm_sum / 10
            self.Vm_10M_average = average
            self.Vm_sum = 0.0
