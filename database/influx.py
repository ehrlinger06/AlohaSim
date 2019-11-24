import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple

import mosaik_api
from influxdb import InfluxDBClient

meta = {
    'models': {
        'Database': {
            'public': True,
            'any_inputs': True,
            'params': ['host', 'port', 'username',
                       'password', 'db_name', 'run_id',
                       'start_timestamp', 'time_unit'],
            'attrs': [],
        },
    },
    'extra_methods': [
        'add_tag',
        'add_component_tag',
        'set_tags',
    ],
}


class Simulator(mosaik_api.Simulator):
    def __init__(self):
        super().__init__(meta)
        self.eid = 'influxdb-collector'
        self.step_size = None
        self.utc_start_timestamp = None
        self.run_id = None
        self.time_unit = None
        self.db_client = None
        self.tags: Dict[Tuple[str, str], Dict[str, str]] = {}
        self.component_tags: Dict[str, Dict[str, str]] = {}

    def init(self, sid, step_size):
        self.step_size = step_size
        return self.meta

    def create(self, num, model, db_name, run_id=str(uuid.uuid4()),
               start_timestamp=datetime.now().isoformat(), time_unit='s',
               host='localhost', port='8086', username='root', password='root'
               ):
        if num != 1 or self.db_client is not None:
            raise RuntimeError('Can only create one instance of MosaikInfluxDBCollector.')
        if model != 'Database':
            raise ValueError('Unknown model: "{0}"'.format(model))

        # Convert params to correct forms
        if time_unit == 's':
            time_unit = timedelta(seconds=1)
        elif 'ms':
            time_unit = timedelta(milliseconds=1)

        # Convert timestamp to UTC
        start_timestamp = datetime.fromisoformat(start_timestamp)
        self.utc_start_timestamp = start_timestamp.astimezone(timezone.utc)
        self.run_id = run_id
        self.time_unit = time_unit

        # Initialize database connection
        self.db_client = InfluxDBClient(host, port, username, password, db_name)
        try:
            self.db_client.ping()
        except Exception as e:
            raise RuntimeError('Initial connection to InfluxDB at {0}:{1} could not be established: {2}'
                               .format(host, port, e))

        # Create the database if non-existent
        existing_db_names = [record['name'] for record in self.db_client.get_list_database()]
        print(existing_db_names)
        if db_name not in existing_db_names:
            self.db_client.create_database(db_name)

        print('Writing to InfluxDB; Run ID:', run_id)
        return [{'eid': self.eid, 'type': model}]

    def step(self, time, inputs):
        data = inputs[self.eid]

        # Respects RFC3999 (timezone in UTC because of +00:00 suffix)
        database_time = (self.utc_start_timestamp + self.time_unit * time).isoformat()
        influx_measurement_jsons = []

        for measurement, values_dict in data.items():
            for component_full_id, value in values_dict.items():
                necessary_tags = {
                    'run_id': self.run_id,
                    'component': component_full_id
                }
                component_tags = self.component_tags.get(component_full_id) or {}
                additional_tags = self.tags.get((component_full_id, measurement)) or {}

                measurement_json = {
                    'measurement': measurement,
                    'tags': {**component_tags, **additional_tags, **necessary_tags},
                    'fields': {
                        'value': value
                    },
                    'time': database_time
                }
                influx_measurement_jsons.append(measurement_json)

        self.db_client.write_points(influx_measurement_jsons)

        return time + self.step_size

    def add_component_tag(self, entity_id, tag_name, tag_value):
        if not isinstance(entity_id, list):
            entity_id = [entity_id]
        for e_id in entity_id:
            if e_id not in self.component_tags:
                self.component_tags[e_id] = {}
            self.component_tags[e_id][tag_name] = tag_value

    def add_tag(self, entity_id, measurement, tag_name, tag_value):
        if not isinstance(measurement, list):
            measurement = [measurement]
        if not isinstance(entity_id, list):
            entity_id = [entity_id]
        id_measurement = [(e, m) for e in entity_id for m in measurement]

        for id_me in id_measurement:
            if id_me not in self.tags:
                self.tags[id_me]: Dict[str, str] = {}
            self.tags[id_me][tag_name] = tag_value

    def set_tags(self, tags: Dict[Tuple[str, str], Dict[str, str]]):
        self.tags = tags


def main():
    desc = "Running the influxDB Connector as Server"
    mosaik_api.start_simulation(Simulator(), desc)