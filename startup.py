import logging
from typing import Dict
from distributed import Worker, Nanny

from stochss_compute.api import start_api
from stochss_compute.api.delegate.dask_delegate import DaskDelegateConfig
from argparse import ArgumentParser, Namespace
from configparser import ConfigParser, NoOptionError, NoSectionError

def main():
    args = parse_args()
    
    if args.host is None:
        flask_host = "localhost"
    else:
        flask_host = args.host

    if args.port is None:
        flask_port = 29681
    else:
        flask_port = int(args.port)

    delegate_config = DaskDelegateConfig()

    if args.daskconfig is not None:
        dask_args = parse_config(args.daskconfig)
        delegate_config.dask_kwargs = dask_args

    if args.daskhost is not None:
        delegate_config.dask_cluster_address = args.daskhost
    if args.daskport is not None:
        delegate_config.dask_cluster_port = args.daskport

    start_api(host=flask_host, port=flask_port, debug=False, delegate_config=delegate_config)

def parse_args() -> Namespace:
    usage = '''
        startup.py -h HOST -p PORT
    '''
    desc = '''
        Server and cache that anonymizes StochSS simulation data. 
    '''
    parser = ArgumentParser(prog='StochSS-Compute', description=desc, add_help=True, usage=usage, conflict_handler='resolve')
    
    parser.add_argument("-h", "--host", required=False,
                        help="The host to use for the flask server. Defaults to localhost.")
    parser.add_argument("-p", "--port", type=int, required=False,
                        help="The port to use for the flask server. Defaults to 29681.")
    parser.add_argument("-H", "--daskhost", type=int, required=False,
                        help="The host to use for the dask scheduler. Defaults to localhost.")
    parser.add_argument("-P", "--daskport", type=int, required=False,
                        help="The port to use for the dask scheduler. Defaults to 8786.")
    parser.add_argument("-D", "--daskconfig", required=False,
                        help="Path to a config file.")
    return parser.parse_args()

def parse_config(path_to_config: str) -> Dict:
    config = ConfigParser(allow_no_value=False, empty_lines_in_values=False)
    config.read(path_to_config)
    dask_args = dict()
    if len(config.sections()) == 0:
        print("Could not read dask config file. Using default values.")
    else:
        for section in config.sections():
            try:
                items = config.items(section)
            except NoSectionError:
                print(f"Could not read dask config file: Key: {section}. Ignoring.")
                continue
            for item in items:
                try:
                    key = item[0]
                    val = item[1]
                    if val == "":
                        continue
                    elif key in ["host", "dashboard_address", "worker_dashboard_address", "protocol", "interface"]:
                        dask_args[key] = config.get(section, key).strip('"\'')
                    elif key in ["scheduler_port", "n_workers", "threads_per_worker"]:
                        dask_args[key] = config.getint(section, key)
                    elif key in ["processes", "asynchronous"]:
                        dask_args[key] = config.getboolean(section, key)
                    elif key == "silence_logs":
                        if "WARN" in val:
                            val = logging.WARNING
                        if "CRITICAL" in val:
                            val = logging.CRITICAL
                        if "ERROR" in val:
                            val = logging.ERROR
                        if "INFO" in val:
                            val = logging.INFO
                        if "NOTSET" in val:
                            val = logging.NOTSET
                        if "DEBUG" in val:
                            val = logging.DEBUG
                        dask_args[key] = val
                    elif key == "worker_class":
                        if "Nanny" in val:
                            dask_args[key] = Nanny
                        if "Worker" in val:
                            dask_args[key] = Worker
                except (NoSectionError, NoOptionError) as e:
                    print(e)
                    print(
                        f"Could not read dask config file: Key: {key}. Value: {val}. Ignoring.")
                    continue


if __name__ == "__main__":
    main()
