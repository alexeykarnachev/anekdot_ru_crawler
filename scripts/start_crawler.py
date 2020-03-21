import argparse
import asyncio
import logging.config
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).parent / '..'))


def _str2path(string: str) -> pathlib.Path:
    return pathlib.Path(string)


def parse_arguments() -> argparse.Namespace:
    default_logs_dir = pathlib.Path(__file__).parent / '../logs'

    parser = argparse.ArgumentParser(
        description='Begins anekdot.ru crawling.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--output_file', type=_str2path, required=True,
        help='Output file, where all parsed content will'
             'be saved.'
    )
    parser.add_argument(
        '--logs_dir', type=_str2path, required=False, default=default_logs_dir,
        help=f'Logs directory.'
    )
    parser.add_argument(
        '--timeout', type=int, required=False, default=30,
        help='Requests timeout, s.'
    )
    parser.add_argument(
        '--concurrency', type=int, required=False, default=10,
        help='Concurrency level.'
    )
    parser.add_argument(
        '--n_retries', type=int, required=False, default=3,
        help='Number of retries if timeout was occurred.'
    )
    args = parser.parse_args()

    return args


def prepare_logging(args):
    """Configures logging."""
    from anekdot_ru_crawler import log_utils as _log
    log_config = _log.get_log_config(log_dir=args.logs_dir)
    logging.config.dictConfig(log_config)


def run_loop(out_file_path, timeout, concurrency):
    """Executes parsing loop."""
    from anekdot_ru_crawler import crawler

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        crawler.crawl(
            start_day=crawler.START_DAY,
            last_day=crawler.get_today(),
            out_file_path=out_file_path,
            timeout=timeout,
            concurrency=concurrency
        )
    )


def main():
    """Parse script arguments, configures logging and begins parsing."""

    args = parse_arguments()
    args.output_file.parent.mkdir(
        exist_ok=True, parents=True
    )
    prepare_logging(args)
    run_loop(
        out_file_path=args.output_file,
        timeout=args.timeout,
        concurrency=args.concurrency
    )


if __name__ == '__main__':
    main()
