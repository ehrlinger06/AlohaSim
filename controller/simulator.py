import mosaik_api

MODEL_NAME = 'Aloha'

meta = {
    'models': {
        'AlohaOben': {
            'public': True,
            'any_inputs': True,
            'params': ['data'],
            'attrs': ['node_id', 'voltage', 'Vm', 'Va', 'P_out', 'Q_out', 'arrival_time', 'departure_time',
                      'available', 'current_soc', 'possible_charge_rate', 'Q'],
        },
    }
}


class AlohaOben:
    def __init__(self, data):
        self.data = data
        self.counter = 0
        # self.val_out = self.data[0]
        self.node_id = data
        self.voltage = 230.0
        self.P_out=5.0
        self.Q_out = 200.0
        self.Vm=230.0

    def step(self, steps, inputs):

        # print("inputs:", inputs)
        #self.counter = (self.counter + steps) % len(self.data)
        self.counter = (self.counter + steps)
        #self.val_out = self.data[self.counter]
        current = list(inputs.keys())
        # print("current:", current)
        # print("node_id:", self.node_id)
        # currentByNodeID = inputs[current[self.node_id]]
        # print("currentByNodeID:", currentByNodeID)
        # alpha = currentByNodeID['Vm']
        # print("alpha:", alpha)
        beta = list(inputs[list(inputs.keys())[self.node_id]]['Vm'].values())[0]
        # print("beta:", beta)
        omega = list(inputs[list(inputs.keys())[self.node_id]]['possible_charge_rate'].values())[0]
        # print("omega:", omega)
        alpha = list(inputs[list(inputs.keys())[self.node_id]]['Q'].values())[0]
        # print("alpha:", alpha)
        Vm = list(inputs[list(inputs.keys())[self.node_id]]['Vm'].values())[0]
        Va = list(inputs[list(inputs.keys())[self.node_id]]['Va'].values())[0]
        Q = list(inputs[list(inputs.keys())[self.node_id]]['Q'].values())[0]
        Q_out = Q
        P_out = Va * Vm
        if self.Vm == Vm:
            print("same")




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

    def create(self, num, model, data=0):
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

                # Get model.val or model.delta:
                # print("self._entities[eid]:", self._entities[eid])
                # print("getattr(models[eid], P_out):", getattr(models[eid], attr))
                # print("getattr(models[eid], departure_time):", getattr(models[eid], 'departure_time'))
                data[eid][attr] = getattr(models[eid], attr)
                # getattr(models[eid])
                # data[eid][attr] = self._entities[eid]
                # print("data[eid][attr]:", data[eid][attr])

        return data
