import arrow

import mosaik_api

__version__ = '1.0.2'

DATE_FORMAT = 'YYYY-MM-DD HH:mm:ss'
# cyclic data from csv files
YEAR = 2014
MONTH = 1
DAY = 1


class CSV(mosaik_api.Simulator):
    def __init__(self):
        super().__init__({'models': {}})
        self.start_date = None
        self.datafile = None
        self.next_row = None
        self.modelname = None
        self.attrs = None
        self.eids = []
        self.cache = None

        self.filename = None

    def init(self, sid, sim_start, datafile):
        self.start_date = arrow.get(sim_start)
        # set date to date of the files
        self.start_date.replace(year=YEAR, month=MONTH, day=DAY)
        self.next_date = self.start_date

        self.filename = datafile

        self.attrs = self._init_csv_file()

        self.meta['models'][self.modelname] = {
            'public': True,
            'params': [],
            'attrs': self.attrs,
        }

        return self.meta

    def create(self, num, model):
        if model != self.modelname:
            raise ValueError('Invalid model "%s" % model')

        start_idx = len(self.eids)
        entities = []
        for i in range(num):
            eid = '%s_%s' % (model, i + start_idx)
            entities.append({
                'eid': eid,
                'type': model,
                'rel': [],
            })
            self.eids.append(eid)
        return entities

    def step(self, time, inputs=None):
        data = self.next_row
        if data is None:
            raise IndexError('End of CSV file reached.')

        # Check date
        date = data[0]
        timeInput = time
        hr = 0
        min = 0
        if time / 3600 >= 1:
            hr = int(time / 3600)
            time = time - (hr * 3600)

        if time / 60 >= 1:
            min = int(time / 60)
            time = time - (min * 60)

        sec = time
        time = timeInput
        expected_date = self.start_date.replace(hour=hr, minute=min, second=sec)
        # set expected date always to start date
        expected_date = expected_date.replace(year=YEAR, month=MONTH, day=DAY)
        if date != expected_date:
            raise IndexError('Wrong date "%s", expected "%s"' % (
                date.format(DATE_FORMAT),
                expected_date.format(DATE_FORMAT)))

        # Put data into the cache for get_data() calls
        self.cache = {}
        for attr, val in zip(self.attrs, data[1:]):
            self.cache[attr] = float(val)

        self._read_next_row()
        if self.next_row is not None:
            return time + 60 #(self.next_row[0].timestamp - date.timestamp)
        else:
            return float('inf')

    def get_data(self, outputs):
        data = {}
        for eid, attrs in outputs.items():
            if eid not in self.eids:
                raise ValueError('Unknown entity ID "%s"' % eid)

            data[eid] = {}
            for attr in attrs:
                data[eid][attr] = self.cache[attr]

        return data

    def _init_csv_file(self):
        self.datafile = open(self.filename)
        self.modelname = next(self.datafile).strip()

        # Get attribute names and strip optional comments
        attrs = next(self.datafile).strip().split(',')[1:]
        for i, attr in enumerate(attrs):
            try:
                # Try stripping comments
                attr = attr[:attr.index('#')]
            except ValueError:
                pass
            attrs[i] = attr.strip()
        self.attrs = attrs

        # Check start date
        self._read_next_row()
        if self.start_date < self.next_row[0]:
            raise ValueError('Start date "%s" not in CSV file.' %
                             self.start_date.format(DATE_FORMAT))
        while self.start_date > self.next_row[0]:
            self._read_next_row()
            if self.next_row is None:
                raise ValueError('Start date "%s" not in CSV file.' %
                                 self.start_date.format(DATE_FORMAT))

        return attrs

    def _read_next_row(self):
        try:
            self.next_row = next(self.datafile).strip().split(',')
            self.next_row[0] = arrow.get(self.next_row[0], DATE_FORMAT)
        except StopIteration:
            self.next_row = None

        # end of file reached -> start from beginning with same time
        if self.next_row is None:
            self.datafile.close()
            self._init_csv_file()


def main():
    return mosaik_api.start_simulation(CSV(), 'controller-csv simulator')
