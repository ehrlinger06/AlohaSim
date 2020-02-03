import random
import versions.adjustedVoltageController_VDE4100 as voltageController_VDE
import versions.adjustedPowerController_own as voltageController_OWN
import versions.tau_vde as tau_vde
import versions.SlottedAloha as pureAloha
import versions.onlyVDE as onlyVDE
import versions.SA_preWaitingSoC as SlottedAloha_preWaitingSoC
import versions.SA_disconnectSoC as SlottedAloha_disconnectSoC
import versions.SA_disconnect5050 as SlottedAloha_disconnect5050
import versions.SA_waitingTime as SlottedAloha_waitingTime
import versions.SA_waitingTime_VDE as SlottedAloha_waitingTime_VDE
import versions.SA_waitingTime_tau as SlottedAloha_waitingTime_tau
import versions.SA_waitingTime_VDE_tau as SlottedAloha_waitingTime_VDE_tau
import versions.TrafoLoad_noEVs as TrafoLoad

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
                      'available', 'current_soc', 'possible_charge_rate', 'Q', 'P', 'P_from', 'Q_from', 'U_s'],
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

        if self.method == 'SlottedAloha':
            self.models[eid] = pureAloha.SlottedAloha_Class(node_id, id=i + start_idx, seed=seed)

        if self.method == 'SlottedAloha_lowestGlobalVoltage':
            self.models[eid] = versions.SA_preWaitingArrivers.SlottedAloha_preWaitingArrivers(node_id, id=i + start_idx,
                                                                                              seed=seed)

        if self.method == 'SlottedAloha_preWaitingArrivers':
            self.models[eid] = versions.SA_preWaitingArrivers.SlottedAloha_preWaitingArrivers(node_id, id=i + start_idx,
                                                                                              seed=seed)
        if self.method == 'SlottedAloha_preWaitingSoC':
            self.models[eid] = SlottedAloha_preWaitingSoC.SlottedAloha_preWaitingSoC(node_id, id=i + start_idx,
                                                                                     seed=seed)

        if self.method == 'SlottedAloha_disconnect5050':
            self.models[eid] = SlottedAloha_disconnect5050.SlottedAloha_disconnect5050(node_id, id=i + start_idx,
                                                                                       seed=seed)
        if self.method == 'SlottedAloha_disconnectSoC':
            self.models[eid] = SlottedAloha_disconnectSoC.SlottedAloha_disconnectSoC(node_id, id=i + start_idx,
                                                                                     seed=seed)

        if self.method == 'SlottedAloha_waitingTime':
            self.models[eid] = SlottedAloha_waitingTime.SlottedAloha_waitingTime(node_id, id=i + start_idx, seed=seed)
        if self.method == 'SlottedAloha_waitingTime_VDE':
            self.models[eid] = SlottedAloha_waitingTime_VDE.SlottedAloha_waitingTime_VDE(node_id, id=i + start_idx,
                                                                                         seed=seed)

        if self.method == 'SlottedAloha_waitingTime_tau':
            self.models[eid] = SlottedAloha_waitingTime_tau.SlottedAloha_waitingTime_tau(node_id, id=i + start_idx,
                                                                                         seed=seed)
        if self.method == 'SlottedAloha_waitingTime_VDE_tau':
            self.models[eid] = SlottedAloha_waitingTime_VDE_tau.SlottedAloha_waitingTime_VDE_tau(node_id,
                                                                                                 id=i + start_idx,
                                                                                                 seed=seed)
        if self.method == 'TrafoLoad':
            self.models[eid] = TrafoLoad.TrafoLoad(node_id, id=i + start_idx, seed=seed)

        if self.method == 'voltageController_VDE':
            self.models[eid] = voltageController_VDE.AdjustedVoltageController(node_id, id=i + start_idx, seed=seed)
        if self.method == 'voltageController_OWN':
            self.models[eid] = voltageController_OWN.AdjustedVoltageController(node_id, id=i + start_idx, seed=seed)
        if self.method == 'tau_VDE':
            self.models[eid] = tau_vde.TauVde(node_id, id=i + start_idx, seed=seed)
        if self.method == 'tau_OWN':
            self.models[eid] = versions.tau_own.TauOwn(node_id, id=i + start_idx, seed=seed)

        return [{'eid': eid, 'type': model}]

    def step(self, time, inputs):
        participants = self.getParticipants(inputs)
        arrivers = self.getArrivers(inputs, time)
        for model in self.models:
            input = inputs.get(model)
            instance = self.models.get(model)
            if self.method == 'SlottedAloha' or self.method == 'SlottedAloha_disconnect5050' \
                    or self.method == 'SlottedAloha_disconnectSoC' or self.method == 'SlottedAloha_waitingTime' \
                    or self.method == 'SlottedAloha_waitingTime_VDE' or self.method == 'SlottedAloha_waitingTime_tau' \
                    or self.method == 'SlottedAloha_waitingTime_VDE_tau':
                instance.step(time, input, participants)
            elif self.method == 'SlottedAloha_lowestGlobalVoltage':
                inputs = self.getMinimalVoltage(inputs)
                instance.step(time, input, arrivers, participants)
            elif self.method == 'TrafoLoad':
                instance.step(input)
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
