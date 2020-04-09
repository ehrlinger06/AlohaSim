import mosaik_api

import versions.SA_participants_VDE_tau as SlottedAloha_participants_VDE_tau
import versions.SA_participants_VDE_tau_trafo as SlottedAloha_participants_VDE_tau_trafo
import versions.SA_waitingTime_VDE_tau as SlottedAloha_waitingTime_VDE_tau
import versions.SA_waitingTime_VDE_tau_trafo as SlottedAloha_waitingTime_VDE_tau_trafo
import versions.tau_VDE_trafo as tau_vde_trafo
import versions.tau_vde as tau_vde

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
        """
        initiates the simulator for the controller instances

        :param sid:
        :param step_size: the step size of one time step
        :param method: the method used by the controllers in this simlation
        :return: the meta informations of this simulator
        """
        self.step_size = step_size
        self.method = method
        return self.meta

    def create(self, num, model, node_id, seed):
        """
        creates a controller instance for use in the simualtion

        :param num: the identification number of this controller
        :param model: the model of the conntroller
        :param node_id: the node the controller works with on in the simulation
        :param seed: the start value for generating random numbers
        :return: a new instance of a controller object, represented by a entry in the self.models-list
        """
        start_idx = len(self._eids)
        i = len(self.models)
        eid = 'Aloha_%s' % (i + start_idx)

        if self.method == 'SlottedAloha_waitingTime_VDE_tau':
            self.models[eid] = SlottedAloha_waitingTime_VDE_tau.\
                SlottedAloha_waitingTime_VDE_tau(node_id, id=i + start_idx, seed=seed)
        if self.method == 'SlottedAloha_waitingTime_VDE_tau_trafo':
            self.models[eid] = SlottedAloha_waitingTime_VDE_tau_trafo. \
                SlottedAloha_waitingTime_VDE_tau_trafo(node_id, id=i + start_idx, seed=seed)

        if self.method == 'SlottedAloha_participants_VDE_tau':
            self.models[eid] = SlottedAloha_participants_VDE_tau. \
                SlottedAloha__participants_VDE_tau(node_id, id=i + start_idx, seed=seed)
        if self.method == 'SlottedAloha_participants_VDE_tau_trafo':
            self.models[eid] = SlottedAloha_participants_VDE_tau_trafo.\
                SlottedAloha__participants_VDE_tau_trafo(node_id, id=i + start_idx, seed=seed)

        if self.method == 'tau_VDE':
            self.models[eid] = tau_vde.TauVde(node_id, id=i + start_idx, seed=seed)
        if self.method == 'tau_VDE_trafo':
            self.models[eid] = tau_vde_trafo.TauVde_Trafo(node_id, id=i + start_idx, seed=seed)

        return [{'eid': eid, 'type': model}]

    def step(self, time, inputs):
        """
        initiates a time step for each instance of the simulator with the input received form other parts
        of the simulator

        :param time: the current time in seconds
        :param inputs: the data received form other parts
        :return: the new time after the step is completed
        """
        participants = self.getParticipants(inputs)
        for model in self.models:
            input = inputs.get(model)
            instance = self.models.get(model)
            if self.method == 'SlottedAloha_waitingTime_VDE_tau' \
                    or self.method == 'SlottedAloha_waitingTime_VDE_tau_trafo' or self.method == 'tau_VDE' \
                    or self.method == 'SlottedAloha_participants_VDE_tau' or self.method == 'SlottedAloha_participants_VDE_tau_trafo'\
                    or self.method == 'tau_VDE_trafo':
                instance.step(time, input, participants)

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

    def getParticipants(self, inputs):
        """
        calculates the amount of participants, which are available and have a state of charge of less than a 100 percent
        :param inputs: the data received form other parts of the simulator
        :return: the amount of participants
        """
        counterPar = 0
        for item in inputs.values():
            if list(item.get('available').values())[0] and list(item.get('current_soc').values())[0] < 100.0:
                counterPar += 1
        return counterPar
