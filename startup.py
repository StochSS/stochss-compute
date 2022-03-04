import logging
from typing import Dict
from distributed import Client, LocalCluster, Worker, Nanny
from webbrowser import open_new

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
        flask_attempt_port = 29681
    else:
        flask_attempt_port = int(args.port)

    if args.daskconfig is not None:
        dask_args = parse_config(args.daskconfig)
    else:
        dask_args = config_dialogue(args)

    dask_cluster = LocalCluster(**dask_args)
    client = Client(dask_cluster)
    print(f"\nDask scheduler at <{dask_cluster.scheduler_address}>")
    print(f"{len(dask_cluster.workers)} Workers")
    print(f"{dask_cluster._threads_per_worker()} threads per Worker")
    
    print(f"Dask dashboard at <{client.dashboard_link}>")
    if not args.nodashboard: 
        print(f"Opening in browser...")
        open_new(client.dashboard_link)
    print()

    dask_port = client.scheduler.addr.split(":")[2]
    dask_host = client.scheduler.addr.split(":")[1]
    delegate_config = DaskDelegateConfig()
    delegate_config.dask_cluster_port = dask_port
    delegate_config.dask_cluster_address = dask_host
    while True:
        try:
            start_api(host=flask_host, port=flask_attempt_port, debug=False, delegate_config=delegate_config)
            client.close()
            break
        except OSError as e:
            if e.errno == 98:
                print(f"Port {flask_attempt_port} in use. Trying {flask_attempt_port + 1}.")
                flask_attempt_port += 1

def parse_args() -> Namespace:
    parser = ArgumentParser()
    parser.add_argument("--host", required=False,
                        help="The host to use for the flask server. Defaults to localhost.")
    parser.add_argument("-p", "--port", type=int, required=False,
                        help="The port to use for the flask server. Defaults to 29681.")
    parser.add_argument("-H", "--dask_host", type=int, required=False,
                        help="The host to use for the dask scheduler. Defaults to localhost.")
    parser.add_argument("-P", "--dask_port", type=int, required=False,
                        help="The port to use for the dask scheduler. Defaults to 8786.")
    parser.add_argument("-D", "--daskconfig", required=False,
                        help="Path to a config file.")
    parser.add_argument("--nodashboard", action='store_true', required=False,
                        help="Start without opening dask dashboard.")
    return parser.parse_args()

def parse_config(path_to_config: str) -> dict:
    config = ConfigParser(allow_no_value=True, empty_lines_in_values=False)
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
                    if val == "None":
                        continue
                    elif key in ["host", "dashboard_address", "worker_dashboard_address", "protocol", "interface"]:
                        dask_args[key] = config.get(section, key).strip('"\'')
                    elif key in ["scheduler_port", "n_workers", "threads_per_worker", ""]:
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
                except (NoSectionError, NoOptionError):
                    print(
                        f"Could not read dask config file: Key: {key}. Value: {val}. Ignoring.")
                    continue

def config_dialogue(args: Namespace) -> dict:
    dask_args = dict()
    while True:
        inp = input("Use default dask settings? y/n\n")
        if inp in ["y", "Y"]:
            if args.dask_host is not None:
                dask_args["host"] = args.dask_host
            if args.dask_port is not None:
                dask_args["scheduler_port"] = args.dask_host
            return dask_args
        elif inp in ["n", "N"]:
            if args.dask_host is None:
                host = input(
                    "Scheduler address? Defaults to localhost. Enter an address or press enter to use default address.\n")
            else:
                host = args.dask_host
            if host != "":
                dask_args["host"] = host
            if args.dask_port is None:
                scheduler_port = input(
                    "Scheduler port? Defaults to 8786. Enter a port or press enter to use default port.\n")
            else:
                scheduler_port = int(args.dask_port)
            if scheduler_port != "":
                dask_args["scheduler_port"] = int(scheduler_port)
            n_workers = input(
                "Number of workers? Defaults to one worker per core. Enter an integer or press enter to use default setting.\n")
            if n_workers != "":
                dask_args["n_workers"] = int(n_workers)
            threads_per_worker = input(
                "Threads per worker? Defaults to 2. Enter an integer or press enter to use default setting.\n")
            if threads_per_worker != "":
                dask_args["threads_per_worker"] = int(threads_per_worker)
            return dask_args
        else:
            continue

if __name__ == "__main__":
    main()
