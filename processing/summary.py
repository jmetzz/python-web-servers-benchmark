#!/usr/bin/env python3

import re
import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import pprint as pp
import logging
import random as rd

from itertools import chain
from collections import defaultdict

logging.basicConfig(level='DEBUG')
logger = logging.getLogger('summary')

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

                if ext == 'log':
                    self._logHandler(file, server, conn, round)
                elif ext == 'stats':
                    self._statsHandler(file, server, conn, round)
                else:
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

    @staticmethod
    def avg(values):
        return sum(values) / float(len(values)) if len(values) > 0 else 0

    def get_data_frame(self, feature, debug=False):
        conn = sorted(list(self._connections))
        servers = list(self._servers)

        feature_average_per_conn = [
            [Parser.avg(self._result.get_values(feature, s, conn))
             for conn in conn] for s in servers
        ]

        df_data = {
            servers[i]: pd.Series(feature_average_per_conn[i], index=conn)
            for i in range(len(feature_average_per_conn))
        }

        df = pd.DataFrame(df_data)
        if debug:
            pp.pprint(df)
        return df

    def get_data_frames(self):
        return {f: self.get_data_frame(f) for f in self.FEATURES.keys()}

    def servers(self):
        return list(self._servers)

    def connections(self):
        return list(self._connections)

    def rounds(self):
        return list(self._rounds)

def to_str(values, separator=','):
    return separator.join(str(cell) for cell in values)


def print_table(feature, servers, col_titles, rows):
    print()
    print(feature)
    header = to_str(col_titles)
    print("{},{}".format('server', header))
    for i in range(len(rows)):
        print("{},{}".format(servers[i], to_str(rows[i])))


def export_chart(path, df, unit, extension='png', sufix=None, linestyles=None):
    fig, ax = plt.subplots(1, 1)
    df.plot(kind='line', use_index=True, title=feature, ax=ax, style=linestyles)
    plt.xlabel('Simultaneous connections')
    plt.ylabel(unit)
    plt.show()
    fig.savefig("{}/{}{}.{}".format(path, feature, sufix, extension), dpi=100)
    plt.close()


def create_styles(num):
    linestyles = [':', '-.', '--', '-']
    markers = ['s', 'o','^','*','+','v','p','h','H','x','d', 'D', '_']
    result = list()
    for i in range(num):
        result.append('{}{}'.format(rd.choice(markers), rd.choice(linestyles)))
    return result


if __name__ == '__main__':
    parser = Parser()
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    ext = sys.argv[3]

    data_frames = parser.process(input_path).get_data_frames()
    styles = create_styles(len(parser.servers()))
    features = Parser.FEATURES.items()
    for (feature, unit) in features:
        export_chart(output_path, data_frames[feature], unit, ext, "-complete", styles)

    few_connections = sorted([c for c in parser._connections if c <= 1000])
    for (feature, unit) in features:
        export_chart(output_path, data_frames[feature].loc[few_connections], unit, ext,
                     "-small", styles)








#
# class Result(object):
#     FEATURES = {'REQUESTS': 'Number',
#                 'LATENCIES': 'Milliseconds',
#                 'CPU': '% - 2 cores',
#                 'MEMORY': 'MB',
#                 'CONNECTION_ERRORS': 'Number',
#                 'READ_ERRORS': 'Number',
#                 'WRITE_ERRORS': 'Number',
#                 'TIMEOUT_ERRORS': 'Number'}
#
#     def __init__(self):
#         self.MEMORY = defaultdict(lambda: defaultdict(list))
#         self.CPU = defaultdict(lambda: defaultdict(list))
#         self.LATENCIES = defaultdict(lambda: defaultdict(list))
#         self.CONNECTION_ERRORS = defaultdict(lambda: defaultdict(list))
#         self.READ_ERRORS = defaultdict(lambda: defaultdict(list))
#         self.WRITE_ERRORS = defaultdict(lambda: defaultdict(list))
#         self.TIMEOUT_ERRORS = defaultdict(lambda: defaultdict(list))
#         self.REQUESTS = defaultdict(lambda: defaultdict(list))
#
#     def log_latency(self, server, connections, value):
#         self.LATENCIES[server][connections].append(value)
#
#     def log_request(self, server, connections, value):
#         self.REQUESTS[server][connections].append(value)
#
#     def log_errors(self, server, connections, values):
#         self.CONNECTION_ERRORS[server][connections].append(values[0])
#         self.READ_ERRORS[server][connections].append(values[1])
#         self.WRITE_ERRORS[server][connections].append(values[2])
#         self.TIMEOUT_ERRORS[server][connections].append(values[3])
#
#     def log_cpu_usage(self, server, connections, value):
#         self.CPU[server][connections].append(value)
#
#     def log_mem_usage(self, server, connections, value):
#         self.MEMORY[server][connections].append(value)
#
#     def servers(self):
#         return list(self.REQUESTS.keys())
#
#     def number_of_records(self):
#         key = list(self.REQUESTS.keys())[0]
#         return list(self.REQUESTS[key].keys())

#
# class Parser(object):
#     data = defaultdict(Result)
#
#     DIGITS_RE = re.compile(r'\d+')
#     LATENCY_RE = re.compile(r'([\d\.]+)(\w+)')
#     MEMORY_RE = re.compile(r'([\d]+[\.\d]*)(\w+)')
#
#     ERROR_LABELS = ['connect', 'read', 'write', 'timeout']
#
#     FEATURES = {'REQUESTS': 'Number',
#                 'LATENCIES': 'Milliseconds',
#                 'CPU': '% - 2 cores',
#                 'MEMORY': 'MB',
#                 'CONNECTION_ERRORS': 'Number',
#                 'READ_ERRORS': 'Number',
#                 'WRITE_ERRORS': 'Number',
#                 'TIMEOUT_ERRORS': 'Number'}
#
#     LATENCY_MULTIPLIERS = {
#         'us': 0.001,
#         'ms': 1.0,
#         's': 1000.0
#     }
#
#     def process(self, directory):
#         for file_name in sorted(os.listdir(directory)):
#             logger.debug("Processing file '{}'".format(file_name))
#             with open(os.path.join(directory, file_name), 'r') as file:
#                 server, round, connections, file_type = self._splitFileName(
#                         file_name)
#
#                 if file_type == 'log':
#                     self._logHandler(round, file, server, connections)
#                 elif file_type == 'stats':
#                     self._statsHandler(round, file, server, connections)
#                 else:
#                     raise ValueError('Unknown type: %s' % file_type)
#
#     def _splitFileName(self, file_name):
#         parts = file_name.split('.')
#         # returns server, round, connections, type
#         return parts[0], int(parts[1]), int(parts[2]), parts[3]
#
#     def _logHandler(self, round, content, server, connections):
#         for line in content:
#             parts = [part for part in line.split(' ') if part]
#             if parts[0] == 'Latency':
#                 digits, unit = self.LATENCY_RE.match(parts[1]).groups()
#                 self.data[round].log_latency(server, connections,
#                                              self._to_latency(digits, unit))
#             elif 'Requests' in parts[0]:
#                 self.data[round].log_request(server, connections,
#                                              float(parts[1]))
#             elif 'Socket' == parts[0]:
#                 values = [int(i) for i in self.DIGITS_RE.findall(line)]
#                 self.data[round].log_errors(server, connections, values)
#
#     def _to_latency(self, digits, unit):
#         return float(digits) * self.LATENCY_MULTIPLIERS[unit]
#
#     def _statsHandler(self, round, content, server, connections):
#         for line in content:
#             parts = [part for part in line.split(' ') if part]
#             if 'CONTAINER' not in parts[0]:
#                 cpu = float(parts[2].rstrip('%'))
#                 mem, unit = self.MEMORY_RE.match(parts[3]).groups()
#                 self.data[round].log_cpu_usage(server, connections, cpu)
#                 self.data[round].log_mem_usage(server, connections, float(mem))


# class Output(object):
#
#     def __init__(self, separator=','):
#         self._servers = []
#         self._connections = []
#         self._separator = separator
#         self._tables = {}
#
#     @staticmethod
#     def avg(data, feature, server, count):
#         values = sorted(
#                 getattr(data[rounds], feature)[server].get(count, 0)
#                 for rounds in data
#         )
#
#         if len(values) > 2:
#             # Remove the extremes
#             values = values[1:-1]
#
#         return sum(values) / float(len(values))
#
#     def get(self, feature):
#         return self._tables[feature]
#
#     def build_tables(self, data):
#         round_data = data[list(data.keys())[0]]
#         self._servers = sorted(round_data.servers())
#         self._connections = sorted(round_data.number_of_records())
#
#         self._tables = {k: self._extract_info(data, k) for (k, v) in
#                         Result.FEATURES.items()}
#
#     def _extract_info(self, results, feature):
#         return [[
#             self.avg(results, feature, server, count)
#             for count in self._connections
#         ] for server in self._servers]

# def build_data_frames(data, col_names, index, debug=False):
#     data_frames = defaultdict(dict)
#     for (k, v) in Result.FEATURES.items():
#         df_data = {col_names[i]: pd.Series(data.get(k)[i], index=index)
#                    for i in range(len(col_names))}
#         df = pd.DataFrame(df_data)
#         data_frames[k] = df
#         if debug:
#             print("---------------------")
#             print(k)
#             pp.pprint(df)
#     return data_frames
