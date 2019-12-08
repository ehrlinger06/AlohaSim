import mosaik_api

MODEL_NAME = 'Aloha'
# TODO currently set here, can come from setup.py
BATTERY_CAPACITY = 40000
# TODO Hier wäre experimentierbedarf?
BUFFER_FACTOR = 0.25
NORM_VOLTAGE = 230
CHARGING_DURATION_PER_CONNECTION = 1200

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
        if powerIndex >= 0 & powerIndex <= 1:
            return powerIndex
        elif powerIndex > 1:
            return 1
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
        # self.val_out = self.data[0]
        self.node_id = node_id
        self.voltage = 230.0
        self.P_out = 0.0
        self.Q_out = 0.0
        self.Vm = 230.0
        self.id = id

    def step(self, steps, inputs):
        # self.setP_out(inputs)
        self.charging = True
        if getAttr('available', inputs):
            if (not self.charging) & self.waitingTime == 0:
                P = calcPower(inputs)
                # was wenn P == 0
                if P > 0:
                    self.P_out = P;
                    self.newCharging = True
                    self.VmOLD = getAttr('Vm', inputs)
                    self.charging = True
                    self.chargingTime = CHARGING_DURATION_PER_CONNECTION
            elif (not self.charging) & self.waitingTime > 0:
                self.waitingTime = self.waitingTime - self.step_size
            elif self.charging & self.newCharging:
                VmDifference = getAttr('Vm', inputs) / self.VmOLD
                # TODO reasonable value(11.5V are 95% of 230V)
                if VmDifference >= 0.95:
                    self.newCharging = False
                    self.chargingTime = self.chargingTime - self.step_size
                    # was wenn P == 0
                else:
                    print()
                    # leistung wegnehmen
                    # wartezeit berechnen
            elif self.charging & self.chargingTime > 0:
                print()
                # leistung berechnen
                # ladezeit erniedrigen
                # wass wenn P ==0
            elif self.charging & self.chargingTime == 0:
                print()
                # leistung wegnehmen
                # wartezeit berechnen






        else:
            print()

    def setP_out(self, inputs):
        if voltageHighEnough(getAttr('Vm', inputs)):
            self.P_out = calcPower(inputs)
        else:
            self.P_out = 0.0


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
