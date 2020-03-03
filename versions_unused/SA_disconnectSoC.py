import versions_unused.SA_preWaitingArrivers as SlottedAloha_preWaitingArrivers
import random

NORM_VOLTAGE = 230
BATTERY_CAPACITY = 36253.11
CHARGE_SPEED = 96
ADDITION_FACTOR_1 = 0.25
ADDITION_FACTOR_2 = 0.4

meta = {
    'versions': {
        'AlohaOben': {
            'public': True,
            'any_inputs': True,
            'params': ['node_id', 'id', 'seed'],
            'attrs': ['node_id', 'voltage', 'Vm', 'Va', 'P_out', 'Q_out', 'arrival_time', 'departure_time',
                      'available', 'current_soc', 'possible_charge_rate', 'Q', 'P'],
        },
    }
}


class SlottedAloha_disconnectSoC(SlottedAloha_preWaitingArrivers.SlottedAloha_preWaitingArrivers):

    def __init__(self, node_id, id, seed):
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
        self.arriverFlag = False
        self.waitingTime = 0
        self.P_old = 0.0
        self.arrivers = 0
        self.participants = 0
        self.seed = seed
        self.disconnectFLAG = False

    def step(self, simTime, inputs, participants):
        self.participants = participants
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

        if P > 0:
            self.P_out = P
            self.P_old = P
            self.chargingFLAG = True
        else:
            print('SlottedAloha: COLLISION')
            self.determineDisconnect(inputs)
            if self.disconnectFLAG:
                self.P_out = 0.0
                self.chargingFLAG = False
                self.waitingTime = self.calculateWaitingTime()
            else:
                self.P_out = self.P_old
                self.chargingFLAG = False

    def determineDisconnect(self, inputs):
        print('SlottedAloha_disconnectSoC: determineDisconnect()')
        remainingLoadingTime = self.calculateLoadingTime(inputs)
        timeUntilDeparture = self.getAtt('departure_time', inputs) - self.time

        if timeUntilDeparture < remainingLoadingTime:  # not enough time left too fully charge
            print('Emergency Level 9999')
            # Stay connected, using the last P_out value calculated, which was greater than 0.0
            return False
        else:  # enough time too fully charge
            if timeUntilDeparture <= (remainingLoadingTime * 2):  # enough time to load between one and two times
                print('Standard level 2')
                random.seed(self.seed)
                result = random.randrange(0, (remainingLoadingTime + 1), 1)
                if result < (remainingLoadingTime / 2):
                    return True
                else:
                    return False
            else:  # enough time to load a minimum of two times
                print('Standard Level 1')
                random.seed(self.seed)
                result = random.randrange(0, (remainingLoadingTime + 1), 1)
                if result < (remainingLoadingTime / 4):
                    return True
                else:
                    return False

    def calculateLoadingTime(self, inputs):
        neededCharge = BATTERY_CAPACITY * (1 - (self.getAtt('current_soc', inputs) / 100))
        return int((neededCharge / (NORM_VOLTAGE * CHARGE_SPEED)) * 60)

    def determineDisconnect2(self, inputs):
        # print('SlottedAloha_disconnectSoC: determineDisconnect()')
        remainingLoadingTime = self.calculateLoadingTime(inputs)
        timeUntilDeparture = self.getAtt('departure_time', inputs) - self.time
        timeSinceArrival = self.time - self.getAtt('arrival_time', inputs)
        availableTime = self.getAtt('departure_time', inputs) - self.time - self.getAtt('arrival_time', inputs)


        if timeUntilDeparture < remainingLoadingTime:  # not enough time left too fully charge
            print('Emergency Level 9999')
            # Stay connected, using the last P_out value calculated, which was greater than 0.0
            return False
        else:  # enough time too fully charge
            result = timeUntilDeparture / remainingLoadingTime
