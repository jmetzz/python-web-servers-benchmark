import coloredlogs
import logging


def add_logging_option_arguments(parser, default=logging.WARNING):
    """Add options to an argument parser to configure logging levels."""

    # arguments for logging configuration
    parser.add_argument(
            '--debug',
            help="Show debugging statements. "
                 "Sets logging level to DEBUG",
            action="store_const",
            dest="loglevel",
            const=logging.DEBUG,
            default=default,
    )
    parser.add_argument(
            '-v', '--verbose',
            help="Be verbose. Sets logging level to INFO",
            action="store_const",
            dest="loglevel",
            const=logging.INFO,
    )


def configure_colored_logging(loglevel):
    field_styles = coloredlogs.DEFAULT_FIELD_STYLES.copy()
    field_styles['asctime'] = {}
    level_styles = coloredlogs.DEFAULT_LEVEL_STYLES.copy()
    level_styles['debug'] = {}
    coloredlogs.install(
            level=loglevel,
            use_chroot=False,
            fmt='%(asctime)s %(levelname)-8s %(name)s  - %(message)s',
            level_styles=level_styles,
            field_styles=field_styles)


