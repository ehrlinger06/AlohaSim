import mosaik_api

meta = {
    'models': {
        'Aloha': {
            'public': True,
            'any_inputs': True,
            'params': ['data'],
            'attrs': ['val_out'],
        },
    }
}


class Aloha:
    def __init__(self, data):
        self.data = data
        self.counter = 0
        self.val_out = self.data[0]

    def step(self, steps):
        self.counter = (self.counter + steps) % len(self.data)
        self.val_out = self.data[self.counter]


class AlohaSim(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(meta)
        self.eid = 'aloha-sim'
        self.step_size = None

    def init(self, sid, step_size):
        self.step_size = step_size
        self.models = {}
        return self.meta

    def create(self, num, model, data):
        if model != 'Aloha':
            raise ValueError('Unknown model: "{0}"'.format(model))

        eid = 'Aloha-{0}'.format(len(self.models))
        self.models[eid] = Aloha(data)
        return [{'eid': eid, 'type': model}]

    def step(self, time, inputs):
        for model in self.models.values():
            model.step(self.step_size)

        return time + self.step_size

    def get_data(self, outputs):
        models = self.models
        data = {}
        for eid, attrs in outputs.items():
            data[eid] = {}
            for attr in attrs:
                if attr not in self.meta['models']['Aloha']['attrs']:
                    raise ValueError('Unknown output attribute: {0}'.format(attr))

                # Get model.val or model.delta:
                data[eid][attr] = getattr(models[eid], attr)

        return data
