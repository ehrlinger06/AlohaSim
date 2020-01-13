import random
import versions.adjustedVoltageController_VDE4100 as voltageController_VDE
import versions.adjustedPowerController_own as voltageController_OWN
import versions.tau_vde as tau_vde
import versions.SlottedAloha as pureAloha
import versions.onlyVDE as onlyVDE

import versions

import mosaik_api

MODEL_NAME = 'Aloha'
meta = {
    'models': {
        'AlohaOben': {
            'public': True,
            'any_inputs': True,
            'params': ['node_id', 'id', 'seed'],
            'attrs': ['node_id', 'voltage', 'Vm', 'Va', 'P_out', 'Q_out', 'arrival_time', 'departure_time',
                      'available', 'current_soc', 'possible_charge_rate', 'Q', 'P'],
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

    def init(self, sid, step_size, method):
        self.step_size = step_size
        self.method = method
        return self.meta

    def create(self, num, model, node_id, seed):
        start_idx = len(self._eids)
        i = len(self.models)
        eid = 'Aloha_%s' % (i + start_idx)
        if self.method == 'onlyVDE':
            self.models[eid] = onlyVDE.onlyVDE(node_id, id=i + start_idx, seed=seed)
        if self.method == 'pure':
            self.models[eid] = pureAloha.PureAloha_Class(node_id, id=i + start_idx, seed=seed)
        if self.method == 'baseLine':
            self.models[eid] = versions.SA_preWaitingArrivers.BaseLine(node_id, id=i + start_idx, seed=seed)
        if self.method == 'voltageController_VDE':
            self.models[eid] = voltageController_VDE.AdjustedVoltageController(node_id, id=i + start_idx, seed=seed)
        if self.method == 'voltageController_OWN':
            self.models[eid] = voltageController_OWN.AdjustedVoltageController(node_id, id=i + start_idx, seed=seed)
        if self.method == 'tau_VDE':
            self.models[eid] = tau_vde.TauVde(node_id, id=i + start_idx, seed=seed)
        if self.method == 'tau_OWN':
            self.models[eid] = versions.tau_own.TauOwn(node_id, id=i + start_idx, seed=seed)
        if self.method == 'lowestVoltage_Base':
            self.models[eid] = versions.SA_preWaitingArrivers.BaseLine(node_id, id=i + start_idx, seed=seed)

        # "tau_VDE", "tau_own"

        return [{'eid': eid, 'type': model}]

    def step(self, time, inputs):

        participants = self.getParticipants(inputs)
        arrivers = self.getArrivers(inputs, time)
        for model in self.models:
            input = inputs.get(model)
            instance = self.models.get(model)
            if self.method == 'pure':
                instance.step(time, input, participants)
            elif self.method == 'lowestVoltage_Base':
                inputs = self.getMinimalVoltage(inputs)
                instance.step(time, input, arrivers, participants)
            else:
                instance.step(time, input, arrivers, participants)

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
            if list(item.get('available').values())[0] & (list(item.get('current_soc').values())[0] < 100.0):
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
