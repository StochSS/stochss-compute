import logging
from distributed import Client, LocalCluster

# from stochss_compute.api import start_api
# from stochss_compute.api.delegate.dask_delegate import DaskDelegateConfig
from argparse import ArgumentParser
from configparser import ConfigParser, NoOptionError, NoSectionError

def main():
    parser = ArgumentParser()
    parser.add_argument("-p", "--port", type=int, required=False,
                        help="The port to use for the flask server. Defaults to 1234.")
    parser.add_argument("--host", required=False,
                        help="The host to use for the flask server. Defaults to localhost.")
    # parser.add_argument("-P", "--daskport", type=int, required=False,
                        # help="The port to use for the dask scheduler. Defaults to 8786.")
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
                    except (NoSectionError, NoOptionError):
                        print(
                            f"Could not read dask config file: Key: {key}. Value: {val}. Ignoring.")
                        continue
    else:
        while True:
            inp = input("Use default settings? y/n")
            if inp in ["y", "Y"]:
                break
            elif inp in ["n", "N"]:
                # do stuff
                break     
            else:    
                continue       
    print(dask_args)
    dask_cluster = LocalCluster(**dask_args)
    client = Client(dask_cluster)
    print(dask_cluster)
    input("Press any key to quit")
    client.close()

    # print(client)
    # dask_port = client.scheduler.addr.split(":")[2]
    # print(dask_port)
    # delegate_config = DaskDelegateConfig()
    # delegate_config.dask_cluster_port = dask_port
    # while True:
    #     try:
    #         start_api(host="0.0.0.0", port=1234, debug=False, delegate_config=delegate_config)
    #         break
    #     except OSError as e:
    #         if e.errno == 98:
    #             print(f"Port {flask_attempt_port} in use. Trying {flask_attempt_port + 1}.")
    #             flask_attempt_port += 1


if __name__ == "__main__":
    main()
