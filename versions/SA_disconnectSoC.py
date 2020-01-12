import versions.SlottedAloha as SlottedAloha
import random

NORM_VOLTAGE = 230

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


class SlottedAloha_disconnectSoC(SlottedAloha):

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

    def determineDisconnect(self):
        random.seed(self.seed)
        result = random.randrange(0, 2, 1)
        if result == 1:
            self.disconnectFLAG = True
        else:
            self.disconnectFLAG = False
