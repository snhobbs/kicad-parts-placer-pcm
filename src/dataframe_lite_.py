import copy

import numpy as np


class DataFrame:
    def __init__(self, data):
        out = {}
        if isinstance(data[0], dict):
            for key in data[0]:
                out[key] = []

            for line in data:
                for key, value in line.items():
                    out[key].append(value)

            data = out

        for key in data:
            out[key] = np.array(data[key])

        assert isinstance(data, dict)
        # for value in data.values():
        #    assert isinstance(value, np.array)
        self._data = copy.deepcopy(data)

    def __repr__(self):
        return f"DataFrameLite: {self._data}"

    @property
    def columns(self):
        return sorted(list(self._data.keys()))

    @columns.setter
    def columns(self, iter):
        new = {}
        for a, b in zip(self.columns, iter):
            new[b] = self._data[a]
        self._data = new

        return list(self._data.keys())

    def __len__(self):
        return len(self._data[self.columns[0]])

    def iterrows(self):
        for i in range(0, len(self)):
            yield i, {key: self._data[key][i] for key in self.columns}

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value
