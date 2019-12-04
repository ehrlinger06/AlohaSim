import mosaik_api

MODEL_NAME = 'Aloha'

meta = {
    'models': {
        'AlohaOben': {
            'public': True,
            'any_inputs': True,
            'params': ['data'],
            'attrs': ['node_id', 'voltage', 'Vm', 'Va', 'P_out', 'Q_out', 'arrival_time', 'departure_time',
                      'available', 'current_soc', 'possible_charge_rate', 'Q', 'P', 'I_real', 'I_imag'],
        },
    }
}


class AlohaOben:
    def __init__(self, data):
        self.data = data
        self.counter = 0
        # self.val_out = self.data[0]
        self.node_id = data
        # self.voltage = 251.0
        self.P_out = 5.0
        self.Q_out = 200.0
        self.Vm = 250.0

    def step(self, steps, inputs):
        self.counter = (self.counter + steps)
        Vm = list(inputs[list(inputs.keys())[self.node_id]]['Vm'].values())[0]
        Va = list(inputs[list(inputs.keys())[self.node_id]]['Va'].values())[0]
        Q = list(inputs[list(inputs.keys())[self.node_id]]['Q'].values())[0]
        P = list(inputs[list(inputs.keys())[self.node_id]]['P'].values())[0]
        I_real = list(inputs[list(inputs.keys())[self.node_id]]['I_real'].values())[0]
        I_imag = list(inputs[list(inputs.keys())[self.node_id]]['I_imag'].values())[0]
        print(self.node_id)
        print("I, real and imag", I_real, I_imag)
        self.voltage = Vm
        Q_out = Q
        # TODO nicht i_real sonder possile charge rate
        self.P_out = I_real * Vm


class AlohaSim(mosaik_api.Simulator):
    def __init__(self):
        # super().__init__({'models': {}})
        super().__init__(meta)
        self._eids = []
        self._entities = {}
        self.step_size = 60
        self.models = {}

    def init(self, sid, step_size):
        self.step_size = step_size
        # self.meta['models'][MODEL_NAME] = {
        #    'public': True,
        #    'params': ['value'],
        #    'attrs': ['node_id', 'voltage', 'Vm', 'Va', 'P_out', 'Q_out', 'arrival_time', 'departure_time',
        #              'available', 'current_soc', 'possible_charge_rate']
        # }
        return self.meta

    def create(self, num, model, data):
        if model != 'AlohaOben':
            raise ValueError('Unknown model: "{0}"'.format(model))

        start_idx = len(self._eids)
        entities = []
        i = len(self.models)
        eid = 'Aloha_%s' % (i + start_idx)
        self.models[eid] = AlohaOben(data)
        # entities.append({
        #    'eid': eid,
        #    'type': model,
        #    'rel': [],
        # })
        # self._eids.append(eid)
        # node_id = i + start_idx
        # self._entities[eid] = node_id

        # eid = 'Aloha-{0}'.format(len(self.models))
        # self.models[eid] = Aloha(data,id)
        return [{'eid': eid, 'type': model}]

    def step(self, time, inputs):
        # print("am I in here?")
        for model in self.models.values():
            model.step(self.step_size, inputs)

        return time + self.step_size

    def get_data(self, outputs):
        models = self.models
        data = {}
        # print(outputs)
        # print(models)
        for eid, attrs in outputs.items():
            data[eid] = {}
            # print("len(attrs): ", len(attrs))
            # print("attrs: ", attrs)
            # print("eid: ", eid)

            for attr in attrs:
                # print("self.meta['models']['Aloha']['attrs']:", self.meta['models']['AlohaOben']['attrs'])
                if attr not in self.meta['models']['AlohaOben']['attrs']:
                    # print("Here")
                    raise ValueError('Unknown output attribute: {0}'.format(attr))

                data[eid][attr] = getattr(models[eid], attr)

        return data
