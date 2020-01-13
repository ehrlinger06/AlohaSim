import mosaik_api
import random

import versions.SA_preWaitingArrivers as SlottedAloha_preWaitingArrivers

NORM_VOLTAGE = 230
BATTERY_CAPACITY = 40000

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


class SlottedAloha_preWaitingSoC(SlottedAloha_preWaitingArrivers.BaseLine):

    def __init__(self, node_id, id, seed):
        self.step_size = 60
        self.node_id = node_id
        self.id = id
        self.seed = seed
        self.participants = 0
        self.chargingFLAG = False
        self.waitingTime = 0
        self.P_out = 0.0
        self.P_old = 0.0
        self.disconnectFLAG = False

    def calculatePreWaitingTime(self, inputs):
        current_soc = self.getAtt('current_soc', inputs)
        socTime = current_soc / 10
        socTimeINT = int(socTime)
        random.seed(self.seed)
        return random.randrange(0, max(socTimeINT, 2), 1)
