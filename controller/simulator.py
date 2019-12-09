import random

import mosaik_api

MODEL_NAME = 'Aloha'
# TODO currently set here, can come from setup.py
BATTERY_CAPACITY = 40000
# TODO Hier wäre experimentierbedarf?
BUFFER_FACTOR_LOW = 0.25
BUFFER_FACTOR_HIGH = 0.5
NORM_VOLTAGE = 230
# TODO charging time in Sekunden, wartezeit in minuten (Schlecht nehme ich an)
CHARGING_DURATION_PER_CONNECTION = 1200
MIDDLE_CHARGING_POWER = 9990
LARGE_DISTANCE = 5
SMALL_DISTANCE = 2

meta = {
    'models': {
        'AlohaOben': {
            'public': True,
            'any_inputs': True,
            'params': ['node_id', 'id'],
            'attrs': ['node_id', 'voltage', 'Vm', 'Va', 'P_out', 'Q_out', 'arrival_time', 'departure_time',
                      'available', 'current_soc', 'possible_charge_rate', 'Q', 'P'],
        },
    }
}


def getAttr(attr, inputDict):
    attrDict = inputDict.get(attr)
    if len(attrDict) == 1:
        attrList = list(attrDict.values())
        if len(attrList) == 1:
            return attrList[0]
        else:
            return -1
    else:
        return -1


def checkAttr(attr):
    if attr == -1:
        return False
    else:
        return True


def calcPower(inputs):
    available = getAttr('available', inputs)
    if available:
        possible_charge_rate = getAttr('possible_charge_rate', inputs)
        Vm = getAttr('Vm', inputs)
        if checkAttr(possible_charge_rate) & checkAttr(Vm):
            # return possible_charge_rate * Vm
            return (possible_charge_rate * calculatePowerIndex(Vm)) * Vm
    return 0.0


def calculatePowerIndex(Vm):
    if voltageHighEnough(Vm):
        powerIndex = 20 * Vm / NORM_VOLTAGE - 17.6
        if (powerIndex >= 0.0) & (powerIndex <= 1.0):
            return powerIndex
        elif powerIndex > 1:
            return 1.0
    return 0


def voltageHighEnough(Vm):
    if Vm > 230 * 0.88:
        return True
    else:
        return False


class AlohaOben:
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

    def step(self, steps, inputs):
        # self.setP_out(inputs)
        # TODO was wenn soc 100% aber leistung liegt an(liegt die noch an
        if getAttr('available', inputs) & (getAttr('current_soc', inputs) < 100.0):
            if (not self.chargingFLAG) & (self.waitingTime == 0):  # not charging right now, but waiting time is over
                self.startCharging(steps, inputs)
            elif (not self.chargingFLAG) & (self.waitingTime > 0):  # not charging right now, waiting time not yet over
                self.waitingTime -= 1
            elif self.chargingFLAG & (self.chargingTime > 0) & (not self.newCharging):  # charging time not over, not in
                # first step
                self.charging(steps, inputs)
            elif self.chargingFLAG & self.newCharging:  # charging just finished first step after beginning
                self.continueAfterFirstStep(steps, inputs)
            elif self.chargingFLAG & (self.chargingTime == 0):  # charging, but charging time is now over
                self.stopCharging(inputs, steps)

    def setP_out(self, inputs):
        if voltageHighEnough(getAttr('Vm', inputs)):
            self.P_out = calcPower(inputs)
        else:
            self.P_out = 0.0

    # sets P_out to zero, sets chargingTime to Zero, sets chargingFLAG to false, calculates waiting period
    def stopCharging(self, inputs, steps):
        self.P_out = 0.0
        self.chargingFLAG = False
        self.calculateWaitingTime(inputs, steps)
        # TODO calculate suitable waiting time... ?DONE?
        self.chargingTime = 0

    # calculates power, sets chargingFLAG newCharging and chargingTime, stores Vm value
    def startCharging(self, steps, inputs):
        P = calcPower(inputs)
        # was wenn P == 0
        if P > 0:
            self.P_out = P;
            self.newCharging = True
            self.VmOLD = getAttr('Vm', inputs)
            self.chargingFLAG = True
            self.chargingTime = CHARGING_DURATION_PER_CONNECTION
        else:
            self.newCharging = False
            self.stopCharging(inputs, steps)

    # calculates current power, lowers chargingtime, initiates charging stop if voltage is too low
    def charging(self, steps, inputs):
        P = calcPower(inputs)
        if P > 0:
            self.P_out = P
            self.chargingTime -= self.step_size
        else:
            self.stopCharging(inputs, steps)

    # checks if charging continues beyond the first circle, by looking at occured voltage drop
    def continueAfterFirstStep(self, steps, inputs):
        VmDifference = getAttr('Vm', inputs) / self.VmOLD
        self.newCharging = False
        # TODO reasonable value(11.5V are 5% of 230V)
        if VmDifference >= 0.95:  # voltage drop within limit, continue charging
            self.charging(steps, inputs)
        else:  # voltage drop too significant, stop charging
            self.stopCharging(inputs, steps)

    # calculates the waitingTime before the next connect, based on a sorting into four scenarios
    def calculateWaitingTime(self, inputs, steps):
        arrival = getAttr('arrival_time', inputs)
        departure = getAttr('departure_time', inputs)
        currentTime = (steps - self.step_size) / self.step_size

        current_soc = getAttr('current_soc', inputs)
        # amount of power needed
        if current_soc < 100:
            if calcPower(inputs) > 0:
                neededcharge = BATTERY_CAPACITY * (1 - (current_soc / 100))
                # in hours
                neededTimeHours = neededcharge / calcPower(inputs)
                # in Minutes
                neededTime = int(neededTimeHours * 60)
                neededTimeBuffered_LOW = neededTime * (1 + BUFFER_FACTOR_LOW)
                neededTimeBuffered_HIGH = neededTime * (1 + BUFFER_FACTOR_HIGH)
            else:
                voltageTooLow = True
                neededcharge = BATTERY_CAPACITY * (1 - (current_soc / 100))
                neededTimeHours = neededcharge / MIDDLE_CHARGING_POWER
                neededTime = int(neededTimeHours * 60)
                neededTimeBuffered_LOW = neededTime * (1 + BUFFER_FACTOR_LOW)
                neededTimeBuffered_HIGH = neededTime * (1 + BUFFER_FACTOR_HIGH)
        else:
            self.waitingTime = departure - currentTime

        # time gone since arrival
        timeSince = currentTime - arrival
        # time until depature
        timeUntil = departure - currentTime

        # # timezone mit priority
        # 0. power too low
        # TODO was tun wenn power zu niedrig
        # 1. timeUntil High enough for BUFFER_FACTOR_HIGH => lowest Priority, highest waiting time
        if timeUntil > neededTimeBuffered_HIGH:
            # 12.5% Chance to connect
            connectingProbability = random.randrange(1, 9, 1)  # 1 out of eight cases
            if connectingProbability == 1:
                self.waitingTime = 0
            else:
                # upper_border = int((timeUntil-neededTimeBuffered_HIGH) / 2)
                self.waitingTime = random.randrange(0, max(int(neededTimeBuffered_HIGH), (SMALL_DISTANCE + 1)),
                                                    SMALL_DISTANCE)
        # 2. timeUntil High enough for BUFFER_FACTOR_LOW => second lowest waiting Priority, medium waiting time
        if (timeUntil > neededTimeBuffered_LOW) & (timeUntil < neededTimeBuffered_HIGH):
            # 20% Chance to connect
            connectingProbability = random.randrange(1, 6, 1)  # 1 out of five cases
            if connectingProbability == 1:
                self.waitingTime = 0
            else:
                # upper_border = int((timeUntil - neededTimeBuffered_LOW) / 2)
                self.waitingTime = random.randrange(0, max(int(neededTimeBuffered_LOW), (LARGE_DISTANCE + 1)),
                                                    LARGE_DISTANCE)
        # 3. timeUntil too low, current_soc over 80% => second highest priority, low to zero waiting time
        if (timeUntil < neededTimeBuffered_LOW) & (getAttr('current_soc', inputs) >= 80):
            # 33% Chance to connect
            connectingProbability = random.randrange(1, 4, 1)  # 1 out of three cases
            if connectingProbability == 1:
                self.waitingTime = 0
            else:
                self.waitingTime = self.step_size * connectingProbability
        # 4. timeUntil too low, current_soc under 80% => highest priority, very low to zero waiting time
        if (timeUntil < neededTimeBuffered_LOW) & (getAttr('current_soc', inputs) < 80):
            # 50% Chance to connect
            connectingProbability = random.randrange(1, 3, 1)  # 1 out of two cases
            if connectingProbability == 1:
                self.waitingTime = 0
            else:
                self.waitingTime = self.step_size


class AlohaSim(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(meta)
        self._eids = []
        self._entities = {}
        self.step_size = 60
        self.models = {}

    def init(self, sid, step_size):
        self.step_size = step_size
        return self.meta

    def create(self, num, model, node_id):
        if model != 'AlohaOben':
            raise ValueError('Unknown model: "{0}"'.format(model))

        start_idx = len(self._eids)
        i = len(self.models)
        eid = 'Aloha_%s' % (i + start_idx)
        self.models[eid] = AlohaOben(node_id, id=i + start_idx)
        return [{'eid': eid, 'type': model}]

    def step(self, time, inputs):
        for model in self.models:
            input = inputs.get(model)
            instance = self.models.get(model)
            instance.step(time, input)

        return time + self.step_size

    def get_data(self, outputs):
        models = self.models
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {}

            for attr in attrs:
                if attr not in self.meta['models']['AlohaOben']['attrs']:
                    raise ValueError('Unknown output attribute: {0}'.format(attr))

                data[eid][attr] = getattr(models[eid], attr)

        return data
