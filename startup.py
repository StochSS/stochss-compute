import logging
from distributed import Client, LocalCluster, Worker, Nanny
from webbrowser import open_new

from stochss_compute.api import start_api
from stochss_compute.api.delegate.dask_delegate import DaskDelegateConfig
from argparse import ArgumentParser
from configparser import ConfigParser, NoOptionError, NoSectionError

def main():
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", type=int, required=False,
                        help="The port to use for the flask server. Defaults to 1234.")
    parser.add_argument("--host", required=False,
                        help="The host to use for the flask server. Defaults to localhost.")
    parser.add_argument("-P", "--dask_port", type=int, required=False,
                        help="The port to use for the dask scheduler. Defaults to 8786.")
    parser.add_argument("-H", "--dask_host", type=int, required=False,
                        help="The port to use for the dask scheduler. Defaults to localhost.")
    parser.add_argument("-D","--daskconfig", required=False,
                        help="The host to use for the dask scheduler. Defaults to localhost.")
    args = parser.parse_args()
    
    flask_attempt_port = 1234
    if args.port is not None:
        flask_attempt_port = args.port
    flask_host = "localhost"
    if args.host is not None:
        flask_host = args.host
    if args.daskconfig is not None:
        config = ConfigParser(allow_no_value=True, empty_lines_in_values=False)
        config.read(args.daskconfig)
        dask_args = dict()
        if len(config.sections()) == 0:
            print("Could not read dask config file. Using default values.")
            config = None
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
                        # print(item)
                        if val == "None":
                            continue
                        elif key in ["host", "dashboard_address", "worker_dashboard_address", "protocol", "interface"]:
                            # print(key)
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
        print(dask_args)
        dask_cluster = LocalCluster(**dask_args)
        print(dask_cluster)
        client = Client(dask_cluster)
    else:
        while True:
            inp = input("Use default settings? y/n\n")
            if inp in ["y", "Y"]:
                client = Client()
                break
            elif inp in ["n", "N"]:
                dask_args = dict()
                host = input("Scheduler address? Defaults to localhost. Enter an address or press enter to use default address.\n")
                if host != "":
                    dask_args["host"] = host
                scheduler_port = input("Scheduler port? Defaults to 8786. Enter a port or press enter to use default port.\n")
                if scheduler_port != "":
                    dask_args["scheduler_port"] = int(scheduler_port)
                n_workers = input("Number of workers? Defaults to one worker per core. Enter an integer or press enter to use default setting.\n")
                if n_workers != "":
                    dask_args["n_workers"] = int(n_workers)
                threads_per_worker = input("Threads per worker? Defaults to 2. Enter an integer or press enter to use default setting.\n")
                if threads_per_worker != "":
                    dask_args["threads_per_worker"] = int(threads_per_worker)
                break     
            else:    
                continue
    print(f"Dash dashboard at {client.dashboard_link}. Opening in browser...")
    open_new(client.dashboard_link)
    # input("Press any key to quit")
    # client.close()

    # print(client)
    dask_port = client.scheduler.addr.split(":")[2]
    dask_host = client.scheduler.addr.split(":")[1]
    # print(dask_port)
    delegate_config = DaskDelegateConfig()
    delegate_config.dask_cluster_port = dask_port
    delegate_config.dask_cluster_address = dask_host
    while True:
        try:
            start_api(host=flask_host, port=flask_attempt_port, debug=False, delegate_config=delegate_config)
            break
        except OSError as e:
            if e.errno == 98:
                print(f"Port {flask_attempt_port} in use. Trying {flask_attempt_port + 1}.")
                flask_attempt_port += 1


if __name__ == "__main__":
    main()
