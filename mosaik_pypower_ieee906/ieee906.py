import csv
import os
import arrow


from mosaik_pypower import resource_db as rdb
import mosaik_pypower_ieee906.mosaik_csv_cyclic

sim_config = {
    'CSV': {
        'python': 'mosaik_pypower_ieee906.mosaik_csv_cyclic:CSV',
    },
    'PyPower': {
        'python': 'mosaik_pypower.mosaik:PyPower',
    }
}

DATE_FORMAT = 'YYYY-MM-DD HH:mm:ss'
TIME_FORMAT = 'HH:mm:ss'
START = '2014-01-01 00:00:00'

this_dir, this_filename = os.path.split(__file__)
DATAFOLDER = this_dir + '/data/'
SHAPE_CONFIG = DATAFOLDER + 'Loads.csv'


def get_load_busses():
    with open(SHAPE_CONFIG, newline='') as csvfile:
        config_reader = csv.reader(csvfile, delimiter=',')
        busses = ['bus_' + row[2] for row in list(config_reader)[3:]]
    return busses

def get_transformer():
    print("hello")


def connect_ieee906(world, start_time=START):
    """
    This method connects a controller-pypower instance with the IEEE 906 Test Feeder and respective loads as controller-csv
    simulators to the provided world.

    :param world: controller world to connect the pypower and csv simulator
    :param start_time: starting time, default 00:00:00
    :return: reference to the grid and houses entities, in order to e.g. connect further simulators or write results to
     a database.
    """
    # add simulators to world config
    world.sim_config.update(sim_config)

    # format and fix time
    start_date = arrow.get(START, DATE_FORMAT)
    start_time = arrow.get(start_time, DATE_FORMAT)
    start_date = start_date.replace(hour=start_time.hour, minute=start_time.minute, second=start_time.second)

    # Start power simulator
    pypower = world.start('PyPower', step_size=60)

    # Feed in the 11 kV level to controller-pypower
    rdb.base_mva[11] = 1

    # Instantiate ieee 906 grid models
    grid = pypower.Grid(gridfile=DATAFOLDER + 'ieee906.json').children
    buses = filter(lambda e: e.type == 'PQBus', grid)
    buses = {b.eid.split('-')[1]: b for b in buses}
    trafo = filter(lambda e: e.type == 'Transformer', grid)
    trafo = {t.eid.split('-')[1]: t for t in trafo}

    # start and connect household loads from profiles
    houses = []
    with open(SHAPE_CONFIG, newline='') as csvfile:
        config_reader = csv.reader(csvfile, delimiter=',')

        i = 1
        for row in list(config_reader)[3:]:
            bus = 'bus_' + row[2]
            shape_file = DATAFOLDER + 'shapes/Load_Profile_pq_' + str(i) + '.csv'

            shapeSim = world.start('CSV', sim_start=start_date.format(), datafile=shape_file)
            loadEntity = shapeSim.Load.create(1)[0]
            world.connect(loadEntity, buses[bus], 'P', 'Q')
            houses.append(loadEntity)
            i = i + 1
    return grid, houses, trafo
