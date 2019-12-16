import socket
import random
import uuid

from mosaik_pypower_ieee906 import ieee906
from datetime import datetime

# from mosaik.util import connect_many_to_one
import mosaik

sim_config = {
    'InfluxDB': {
        'python': 'database.influx:Simulator'
    },
    'FlexEVSim': {
        'cmd': 'java -ea -jar ..\AlohaSim\FlexEV\mosaik-flexev-1.1.2.jar %(addr)s'
    },
    'AlohaSim': {
        'python': 'controller.simulator:AlohaSim'
    }

}

START = '2019-11-18 00:00:00'
END = '2019-11-20 00:00:00'
DIFF = datetime.fromisoformat(END.replace(' ', 'T')) - datetime.fromisoformat(START.replace(' ', 'T'))
DURATION = DIFF.total_seconds()
GRID_NAME = 'ieee906'

scenarios = [5]
speeds = [96]
limits = [250]
# "baseLine", "voltageController_VDE", "voltageController_OWN", "tau_VDE", "tau_own"
methods = ["tau_VDE"]



def get_free_tcp_port():
    tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp.bind(('', 0))
    addr, port = tcp.getsockname()
    tcp.close()
    return port


def main():
    print("in Main")
    mosaik_config = {'addr': ('127.0.0.1', get_free_tcp_port())}
    world = mosaik.World(sim_config, mosaik_config=mosaik_config)
    create_scenario(world, GRID_NAME, scenarios[0], charge_speed=speeds[0], method=methods[0], limit=limits[0],
                    seed=42,
                    influxdb=True)
    world.run(until=DURATION)  # As fast as possilbe
    world.shutdown()  # delete world again


def create_scenario(world, grid_name, scenario, charge_speed, method, limit, seed, influxdb=True):
    grid_file = 'data/%s.json' % grid_name

    # Start simulators
    flexev = world.start("FlexEVSim", sim_start=START)
    aloha = world.start("AlohaSim", step_size=60, method=method)

    grid, houses = ieee906.connect_ieee906(world, start_time=START)
    evs = ieee906.get_load_busses()

    random.seed(42)
    random.shuffle(evs)

    #controllers = []
    #for node_id in evs:
    #    controllers.append(aloha.AlohaOben(node_id=node_id))
    controllers = [aloha.AlohaOben(node_id=node_id) for node_id in evs]

    evflexs = [flexev.FlexEV(node_id=node_id, max_charge_rate=charge_speed).children[0] for node_id in evs]

    connect_cs_to_grid(world, controllers, evflexs, grid)

    if influxdb:
        influxdb_collector_sim = world.start('InfluxDB', step_size=60)
        influxdb_collector = influxdb_collector_sim.Database(
            db_name='aloha_test_3',
            run_id=str(uuid.uuid4()),
            start_timestamp=START.replace(' ', 'T'),
            time_unit='s',
            host='localhost',
            port='8086',
            username='root',
            password='root'
        )
        #print("here")
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

        # Add General Tag to all entities
        influxdb_collector_sim.add_component_tag(all_ids, 'scenario', str(scenario))
        influxdb_collector_sim.add_component_tag(all_ids, 'speed', str(charge_speed))
        influxdb_collector_sim.add_component_tag(all_ids, 'limit', str(limit))
        influxdb_collector_sim.add_component_tag(all_ids, 'method', method)

        if method == 'BASE':
            # add tags for all configs, as they do not differ
            [influxdb_collector_sim.add_component_tag(all_ids, 'scenario', str(s)) for s in scenarios]
            [influxdb_collector_sim.add_component_tag(all_ids, 'speed', str(sp)) for sp in speeds]
            [influxdb_collector_sim.add_component_tag(all_ids, 'limit', str(l)) for l in limits]


def connect_cs_to_grid(world, controllers, evs, grid):

    # Connect bus to controller
    buses = filter(lambda e: e.type == 'PQBus', grid)
    buses = {b.eid.split('-')[1]: b for b in buses}
    c_data = world.get_data(controllers, 'node_id')
    for c in controllers:
        node_id = c_data[c]['node_id']
        world.connect(buses[node_id], c, 'Vm', 'Va')

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