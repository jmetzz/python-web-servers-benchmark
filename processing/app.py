#!/usr/bin/env python3

import argparse
import logging
import random as rd
import matplotlib.pyplot as plt

from processing import config, common
from processing.adapter import Parser

logger = logging.getLogger(__name__)

def export_chart(path, df, unit, extension='png', sufix=None, linestyles=None):
    fig, ax = plt.subplots(1, 1)
    df.plot(kind='line', use_index=True, title=feature, ax=ax, style=linestyles)
    plt.xlabel('Simultaneous connections')
    plt.ylabel(unit)
    # Place a legend to the right of this smaller subplot.
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.show()
    fig.savefig("{}/{}{}.{}".format(path, feature, sufix, extension), dpi=100)
    plt.close()


def create_styles(num):
    linestyles = [':', '-.', '--', '-']
    markers = ['s', 'o', '^', '*', '+', 'v', 'p', 'h', 'H', 'x', 'd', 'D', '_']
    result = list()
    for i in range(num):
        result.append('{}{}'.format(rd.choice(markers), rd.choice(linestyles)))
    return result


def create_argument_parser():
    cmd_parser = argparse.ArgumentParser(
            description='Run benchmark analyser and generate chart')

    cmd_parser.add_argument('-i', '--input',
                            required=True,
                            type=str,
                            help='Where to fetch the log files from')
    cmd_parser.add_argument('-o', '--output',
                            required=True,
                            type=str,
                            help='Where to save the charts')
    cmd_parser.add_argument('-e', '--extension',
                            default="png",
                            choices=['png', 'pdf', 'svg', 'ps'],
                            help='The file format to export')

    config.add_logging_option_arguments(cmd_parser)
    return cmd_parser


if __name__ == '__main__':
    args = create_argument_parser().parse_args()
    config.configure_colored_logging(args.loglevel)

    ext = args.extension
    input = args.input
    output = args.output

    parser = Parser()
    data_frames = parser.process(args.input).get_data_frames()
    features = Parser.FEATURES.items()
    styles = create_styles(len(parser.servers()))

    for (feature, unit) in features:
        export_chart(output, data_frames[feature], unit, ext, "", styles)
