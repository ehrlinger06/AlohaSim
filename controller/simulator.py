import random
import versions.BaseLine as baseLine
import versions.adjustedVoltageController_VDE4100 as voltageController_VDE
import versions.adjustedPowerController_own as voltageController_OWN

import mosaik_api

MODEL_NAME = 'Aloha'


class AlohaSim(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(meta)
        self._eids = []
        self._entities = {}
        self.step_size = 60
        self.models = {}
        self.method = 'baseline'

    def init(self, sid, step_size, method):
        self.step_size = step_size
        self.method = method
        return self.meta

    def create(self, num, model, node_id):
        start_idx = len(self._eids)
        i = len(self.models)
        eid = 'Aloha_%s' % (i + start_idx)
        if self.method == 'baseline':
            self.models[eid] = baseLine.BaseLine(node_id, id=i + start_idx)
        if self.method == 'voltageController_VDE':
            self.models[eid] = voltageController_VDE.AdjustedVoltageController(node_id, id=i + start_idx)
        if self.method == 'voltageController_OWN':
            self.models[eid] = voltageController_OWN.AdjustedVoltageController(node_id, id=i + start_idx)
        # "tau_VDE", "tau_own"

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
