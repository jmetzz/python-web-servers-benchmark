import re
import os
import pandas as pd
import logging
from itertools import chain
from collections import defaultdict

from processing import common

logger = logging.getLogger(__name__)


class Result(object):
    def __init__(self):
        self._registry = {}

    def append(self, feature, server, conn, round, value):
        if feature not in self._registry:
            self._registry[feature] = defaultdict(
                    lambda: defaultdict(lambda: defaultdict(list)))
        values = self._registry[feature][server][conn][round]
        values.append(value)

    def get_values(self, feature, server, conn):
        # if l is not None else [0]
        lists = [l for l in self._registry[feature][server][conn].values()]
        return list(chain.from_iterable(lists))


class Parser(object):
    DIGITS_RE = re.compile(r'\d+')
    LATENCY_RE = re.compile(r'([\d\.]+)(\w+)')
    MEMORY_RE = re.compile(r'([\d]+[\.\d]*)(\w+)')

    ERROR_LABELS = ['connect', 'read', 'write', 'timeout']

    FEATURES = {'REQUESTS': 'Number',
                'LATENCY': 'Milliseconds',
                'CPU': '% - 2 cores',
                'MEMORY': 'MB',
                'CONNECTION_ERRORS': 'Number',
                'READ_ERRORS': 'Number',
                'WRITE_ERRORS': 'Number',
                'TIMEOUT_ERRORS': 'Number'}

    LATENCY_MULTIPLIERS = {
        'us': 0.001,
        'ms': 1.0,
        's': 1000.0
    }

    def __init__(self, separator=','):
        self._result = Result()
        self._rounds = set()
        self._servers = set()
        self._connections = set()
        self._separator = separator

    def process(self, directory):
        for file_name in sorted(os.listdir(directory)):
            logger.debug("Processing file '{}'".format(file_name))
            with open(os.path.join(directory, file_name), 'r') as file:
                server, round, conn, ext = self._collect_metadata(file_name)

                logging.info("processing file '{}'".format(file_name))

                if ext == 'log':
                    self._logHandler(file, server, conn, round)
                elif ext == 'stats':
                    self._statsHandler(file, server, conn, round)
                else:
                    logging.error("Invalid file '{}'".format(file_name))
                    raise ValueError('Unknown type: %s' % ext)
        return self

    def _collect_metadata(self, file_name):
        parts = file_name.split('.')
        server, round, conn, type = parts[0], int(parts[1]), int(parts[2]), \
                                    parts[3]
        self._rounds.add(round)
        self._servers.add(server)
        self._connections.add(conn)
        return server, round, conn, type

    def _logHandler(self, content, server, connections, round):
        for line in content:
            parts = [part for part in line.split(' ') if part]
            if parts[0] == 'Latency':
                digits, unit = self.LATENCY_RE.match(parts[1]).groups()
                self._result.append('LATENCY', server, connections, round,
                                    self._to_latency(digits, unit))
            elif 'Requests' in parts[0]:
                self._result.append('REQUESTS', server, connections, round,
                                    float(parts[1]))
            elif 'Socket' == parts[0]:
                values = [int(i) for i in self.DIGITS_RE.findall(line)]
                self._result.append('CONNECTION_ERRORS', server, connections,
                                    round, values[0])
                self._result.append('READ_ERRORS', server, connections, round,
                                    values[1])
                self._result.append('WRITE_ERRORS', server, connections, round,
                                    values[2])
                self._result.append('TIMEOUT_ERRORS', server, connections,
                                    round, values[3])

    def _statsHandler(self, content, server, connections, round):
        for line in content:
            parts = [part for part in line.split(' ') if part]
            # if 'CONTAINER' not in parts[0]:
            if 'CONTAINER' in parts[0]:
                continue
            if len(parts) != 14:
                continue
            cpu = float(parts[2].rstrip('%'))
            mem, unit = self.MEMORY_RE.match(parts[3]).groups()
            self._result.append('CPU', server, connections, round, cpu)
            self._result.append('MEMORY', server, connections, round,
                                float(mem))

    def _to_latency(self, digits, unit):
        return float(digits) * self.LATENCY_MULTIPLIERS[unit]

    def get_data_frame(self, feature):
        conn = sorted(list(self._connections))
        servers = sorted(list(self._servers))

        feature_average_per_conn = [
            [common.avg(self._result.get_values(feature, s, conn))
             for conn in conn] for s in servers
        ]

        df_data = {
            servers[i]: pd.Series(feature_average_per_conn[i], index=conn)
            for i in range(len(feature_average_per_conn))
        }

        df = pd.DataFrame(df_data)
        return df

    def get_data_frames(self):
        return {f: self.get_data_frame(f) for f in self.FEATURES.keys()}

    def servers(self):
        return list(self._servers)

    def connections(self):
        return list(self._connections)

    def rounds(self):
        return list(self._rounds)
