import mosaik_api



MODEL_NAME = 'Aloha'


class Aloha:
    def __init__(self, data, id):
        self.data = data
        self.counter = 0
        self.val_out = self.data[0]
        self.node_id = 17

    def step(self, steps):
        self.counter = (self.counter + steps) % len(self.data)
        self.val_out = self.data[self.counter]


class AlohaSim(mosaik_api.Simulator):
    def __init__(self):
        super().__init__({'models': {}})
        self._eids = []
        self._entities = {}
        self.step_size = 60

    def init(self, sid, step_size):
        self.step_size = step_size
        self.models = {}
        self.meta['models'][MODEL_NAME] = {
            'public': True,
            'params': ['value'],
            'attrs': ['node_id', 'voltage', 'Vm', 'Va', 'P_out', 'Q_out', 'arrival_time', 'departure_time',
                      'available', 'current_soc', 'possible_charge_rate']
        }
        return self.meta

    def create(self, num, model, value=0):
        if model != 'Aloha':
            raise ValueError('Unknown model: "{0}"'.format(model))

        start_idx = len(self._eids)
        entities = []
        for i in range(num):
            eid = 'Aloha_%s' % (i + start_idx)
            entities.append({
                'eid': eid,
                'type': model,
                'rel': [],
            })
            self._eids.append(eid)
            node_id = i + start_idx
            self._entities[eid] = node_id

        #eid = 'Aloha-{0}'.format(len(self.models))
        #self.models[eid] = Aloha(data,id)
        return entities

    def step(self, time, inputs):
        for model in self.models.values():
            model.step(self.step_size)

        return time + self.step_size

    def get_data(self, outputs):
        models = self.models
        data = {}
        #print(outputs)
        #print(models)
        for eid, attrs in outputs.items():
            data[eid] = {}
            #print("len(attrs): ", len(attrs))
            #print("attrs: ", attrs)
            #print("eid: ", eid)

            for attr in attrs:
                #print("attr:", attr)
                if attr not in self.meta['models']['Aloha']['attrs']:
                    #print("Here")
                    raise ValueError('Unknown output attribute: {0}'.format(attr))

                # Get model.val or model.delta:
                #data[eid][attr] = getattr(models[eid], attr)
                data[eid][attr] = self._entities[eid]
                #print("data[eid][attr]:", data[eid][attr])

        return data
