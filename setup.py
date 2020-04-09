import random
import socket
from datetime import datetime
import CollisionCounter as CollisionCounter

import mosaik

from mosaik_pypower_ieee906 import ieee906

sim_config = {
    'InfluxDB': {
        'python': 'database.influx:Simulator'
    },
    'FlexEVSim': {
        'cmd': 'java -ea -jar ..\AlohaSim\FlexEV\mosaik-flexev-1.1.4.jar %(addr)s'
    },
    'AlohaSim': {
        'python': 'controller.simulator:AlohaSim'
    }

}

START = '2019-11-17 00:00:00'
END = '2019-11-18 00:00:00'
DIFF = datetime.fromisoformat(END.replace(' ', 'T')) - datetime.fromisoformat(START.replace(' ', 'T'))
DURATION = DIFF.total_seconds()
GRID_NAME = 'ieee906'

BATTERY_CAPACITY = 36253.11

# RANDOM
seed = 41  # 7, 17, 29, 41, 53, 67, 79, 97, 107, 127
# RANDOM
speed = 96
method = 'SlottedAloha_participants_VDE_tau'
run_nr = 8


# 'tau_VDE', 'tau_VDE_trafo'
# 'SlottedAloha_participants_VDE_tau', 'SlottedAloha_participants_VDE_tau_trafo'
# 'SlottedAloha_waitingTime_VDE_tau', 'SlottedAloha_waitingTime_VDE_tau_trafo',
# 'TrafoLoad'

def get_free_tcp_port():
    """
    searches a free tcp-port and returns the portnumber
    :return: the number of a free tcp port
    """
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(('', 0))
    addr, port = tcp.getsockname()
    tcp.close()
    return port


def main():
    """
    sets up und runs a mosaik world with a scenario in it, layed out by the parameters set earlier.
    """
    mosaik_config = {'addr': ('127.0.0.1', get_free_tcp_port())}
    world = mosaik.World(sim_config, mosaik_config=mosaik_config)
    create_scenario(world, GRID_NAME, charge_speed=speed, method=method, seed=seed, influxdb=True)
    print("Starting method ", method, " with seed ", seed)
    world.run(until=DURATION)  # As fast as possilbe
    world.shutdown()  # delete world again
    CollisionCounter.CollisionCounter.getInstance().printResults()
    print("Finished method ", method, " with seed ", seed)


def create_scenario(world, grid_name, charge_speed, method, seed, influxdb=True):
    """
    starts the three contained simulators(FlexEV, Aloha and IEEE906) withe the needed parameters, connects the
    simulators with each other where necessary
    :param world: a mosaik world object
    :param grid_name: the name of the used power grid
    :param charge_speed: the maximum possible charge speed
    :param method: the method used in this simulation
    :param seed: the start value for generating random numbers
    :param influxdb: a flag, that indicates if te results are stored in an influxdb database
    """
    grid_file = 'data/%s.json' % grid_name

    # Start simulators
    flexev = world.start("FlexEVSim")
    aloha = world.start("AlohaSim", step_size=60, method=method)

    # collect grid informations
    grid, houses, trafo = ieee906.connect_ieee906(world, start_time=START)
    evs = ieee906.get_load_busses()

    random.seed(42)
    random.shuffle(evs)
    evs = evs + evs

    controllers = [aloha.AlohaOben(node_id=node_id, seed=seed) for node_id in evs]

    evflexs = [
        flexev.FlexEV(node_id=node_id, max_charge_rate=charge_speed, battery_capacity=BATTERY_CAPACITY).children[0] for
        node_id in evs]

    connect_cs_to_grid(world, controllers, evflexs, grid, trafo)

    # if true, establishes connection to a running influxdb entity to store results
    if influxdb:
        influxdb_collector_sim = world.start('InfluxDB', step_size=60)
        influxdb_collector = influxdb_collector_sim.Database(
            db_name='aloha_test_12',
            run_id=method + str(run_nr),
            start_timestamp=START.replace(' ', 'T'),
            time_unit='s',
            host='localhost',
            port='8086',
            username='root',
            password='root'
        )
        # Store data on FlexEVs for evaluation
        mosaik.util.connect_many_to_one(world, evflexs, influxdb_collector, 'P', 'current_soc', 'leaving_soc',
                                        'available', 'Q', 'voltage', 'possible_charge_rate')
        all_ids = [e.full_id for e in evflexs]
        ev_flex_data = world.get_data(evflexs, 'node_id')
        for ev_flex in evflexs:
            node_id = ev_flex_data[ev_flex]['node_id']
            influxdb_collector_sim.add_component_tag(ev_flex.full_id, 'node_id', node_id)

        # Store data on Voltage levels in the grid
        buses = filter(lambda e: e.type == 'PQBus', grid)
        buses = {b.eid.split('-')[1]: b for b in buses}
        buses_e = [buses[n] for n in evs]
        mosaik.util.connect_many_to_one(world, buses_e, influxdb_collector, 'Vm')
        all_ids = all_ids + [e.full_id for e in buses_e]
        for bus in buses_e:
            node_id = bus.eid.split('-')[1]
            influxdb_collector_sim.add_component_tag(bus.full_id, 'node_id', node_id)

        # store my own values
        mosaik.util.connect_many_to_one(world, controllers, influxdb_collector, 'Vm_10M_average', 'S')
        controller_data = world.get_data(controllers, 'node_id')
        for controller in controllers:
            node_id = controller_data[controller]['node_id']
            influxdb_collector_sim.add_component_tag(controller.full_id, 'node_id', node_id)

        # Add General Tag to all entities
        influxdb_collector_sim.add_component_tag(all_ids, 'seed', str(seed))
        influxdb_collector_sim.add_component_tag(all_ids, 'speed', str(charge_speed))
        influxdb_collector_sim.add_component_tag(all_ids, 'method', method)
        influxdb_collector_sim.add_component_tag(all_ids, 'run_nr', run_nr)


def connect_cs_to_grid(world, controllers, evs, grid, trafo):
    """
    establshes the connections betwenn the different instances of the simulators.

    :param world: a mosaik world object
    :param controllers: a list of controller-objects
    :param evs: a list of ev-objects
    :param grid: the powergrid used in the scenario
    :param trafo: the Transformer of the used power grid
    """
    # Connect bus to controller
    buses = filter(lambda e: e.type == 'PQBus', grid)
    buses = {b.eid.split('-')[1]: b for b in buses}
    c_data = world.get_data(controllers, 'node_id')
    for c in controllers:
        node_id = c_data[c]['node_id']
        world.connect(buses[node_id], c, 'Vm', 'Va')

    # connect trafo to controllers
    for c in controllers:
        world.connect(trafo['transformer'], c, 'P_from', 'Q_from')

    # connect controller to evs
    ev_data = world.get_data(evs, 'node_id')
    ev_by_node_id = {ev_data[ev]['node_id']: [] for ev in evs}
    for ev in evs:
        node_id = ev_data[ev]['node_id']
        ev_by_node_id[node_id].append(ev)
    for c in controllers:
        node_id = c_data[c]['node_id']
        ev = ev_by_node_id[node_id].pop(0)
        world.connect(c, ev, ('P_out', 'P'), ('Q_out', 'Q'), ('Vm', 'voltage'))
        world.connect(ev, c, 'arrival_time', 'departure_time', 'available', 'current_soc', 'possible_charge_rate',
                      time_shifted=True,
                      initial_data={'arrival_time': -1, 'departure_time': -1, 'available': False, 'current_soc': -1,
                                    'possible_charge_rate': -1})

    # connect evs to grid bus
    for ev in evs:
        node_id = ev_data[ev]['node_id']
        world.connect(ev, buses[node_id], 'P', 'Q', time_shifted=True, initial_data={'P': 0.0, 'Q': 0.0})


main()
