import mosaik_api

import versions.SA_participants_VDE_tau as SlottedAloha_participants_VDE_tau
import versions.SA_participants_VDE_tau_trafo as SlottedAloha_participants_VDE_tau_trafo
import versions.SA_waitingTime as SlottedAloha_waitingTime
import versions.SA_waitingTime_VDE_tau as SlottedAloha_waitingTime_VDE_tau
import versions.SA_waiting_new as SlottedAloha_waiting_new
import versions.SA_waitingTime_VDE_tau_trafo as SlottedAloha_waitingTime_VDE_tau_trafo
import versions.SlottedAloha as pureAloha
import versions.TrafoLoad_noEVs as TrafoLoad
import versions.tau_vde as tau_vde
import versions.tau_VDE_trafo as tau_vde_trafo

MODEL_NAME = 'Aloha'
meta = {
    'models': {
        'AlohaOben': {
            'public': True,
            'any_inputs': True,
            'params': ['node_id', 'id', 'seed'],
            'attrs': ['node_id', 'voltage', 'Vm', 'Va', 'P_out', 'Q_out', 'arrival_time', 'departure_time',
                      'available', 'current_soc', 'possible_charge_rate', 'Q', 'P', 'P_from', 'Q_from', 'U_s',
                      'Vm_10M_average', 'S'],
        },
    }
}


class AlohaSim(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(meta)
        self._eids = []
        self._entities = {}
        self.step_size = 60
        self.models = {}
        self.method = 'baseLine'
        self.collisionCounter = 0

    def init(self, sid, step_size, method):
        self.step_size = step_size
        self.method = method
        return self.meta

    def create(self, num, model, node_id, seed):
        start_idx = len(self._eids)
        i = len(self.models)
        eid = 'Aloha_%s' % (i + start_idx)

        if self.method == 'SlottedAloha':
            self.models[eid] = pureAloha.SlottedAloha_Class(node_id, id=i + start_idx, seed=seed)

        if self.method == 'SlottedAloha_waitingTime':
            self.models[eid] = SlottedAloha_waitingTime.SlottedAloha_waitingTime(node_id, id=i + start_idx, seed=seed)

        if self.method == 'SlottedAloha_waitingTime_VDE_tau':
            self.models[eid] = SlottedAloha_waitingTime_VDE_tau.\
                SlottedAloha_waitingTime_VDE_tau(node_id, id=i + start_idx, seed=seed)
        if self.method == 'SlottedAloha_waiting_new':
            self.models[eid] = SlottedAloha_waiting_new.\
                SlottedAloha_waiting_new(node_id, id=i + start_idx, seed=seed)
        if self.method == 'SlottedAloha_waitingTime_VDE_tau_trafo':
            self.models[eid] = SlottedAloha_waitingTime_VDE_tau_trafo. \
                SlottedAloha_waitingTime_VDE_tau_trafo(node_id, id=i + start_idx, seed=seed)

        if self.method == 'SlottedAloha_participants_VDE_tau':
            self.models[eid] = SlottedAloha_participants_VDE_tau. \
                SlottedAloha__participants_VDE_tau(node_id, id=i + start_idx, seed=seed)
        if self.method == 'SlottedAloha_participants_VDE_tau_trafo':
            self.models[eid] = SlottedAloha_participants_VDE_tau_trafo.\
                SlottedAloha__participants_VDE_tau_trafo(node_id, id=i + start_idx, seed=seed)

        if self.method == 'TrafoLoad':
            self.models[eid] = TrafoLoad.TrafoLoad(node_id, id=i + start_idx, seed=seed)

        if self.method == 'tau_VDE':
            self.models[eid] = tau_vde.TauVde(node_id, id=i + start_idx, seed=seed)
        if self.method == 'tau_VDE_trafo':
            self.models[eid] = tau_vde_trafo.TauVde_Trafo(node_id, id=i + start_idx, seed=seed)

        return [{'eid': eid, 'type': model}]

    def step(self, time, inputs):
        participants = self.getParticipants(inputs)
        arrivers = self.getArrivers(inputs, time)
        for model in self.models:
            input = inputs.get(model)
            instance = self.models.get(model)
            if self.method == 'SlottedAloha' or self.method == 'SlottedAloha_waitingTime_VDE_tau' \
                    or self.method == 'SlottedAloha_waitingTime_VDE_tau_trafo' or self.method == 'tau_VDE' \
                    or self.method == 'SlottedAloha_participants_VDE_tau' or self.method == 'SlottedAloha_participants_VDE_tau_trafo'\
                    or self.method == 'tau_VDE_trafo':
                instance.step(time, input, participants)
            elif self.method == 'SlottedAloha_lowestGlobalVoltage':
                inputs = self.getMinimalVoltage(inputs)
                instance.step(time, input, arrivers, participants)
            elif self.method == 'TrafoLoad':
                instance.step(input, time)
            else:
                instance.step(time, input, arrivers, participants)
            # self.collisionCounter += instance.collisionCounter
        # print("simulator.collisionCounter:", self.collisionCounter)

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

    def getArrivers(self, inputs, time):
        counterArr = 0
        timeMin = ((time - self.step_size) / self.step_size)
        for item in inputs.values():
            arrival_time = list(item.get('arrival_time').values())[0]
            if timeMin == arrival_time:
                counterArr += 1
        return counterArr

    def getParticipants(self, inputs):
        counterPar = 0
        for item in inputs.values():
            if list(item.get('available').values())[0] and list(item.get('current_soc').values())[0] < 100.0:
                counterPar += 1
        return counterPar

    def getMinimalVoltage(self, inputs):
        minVm = -1
        for item in inputs.values():
            Vm = list(item.get('Vm').values())[0]
            if minVm == -1:
                minVm = Vm
            else:
                minVm = min(minVm, Vm)

        for item in inputs.values():
            innerDict = item.get('Vm')
            innerDict[list(innerDict.keys())[0]] = minVm
        return inputs
