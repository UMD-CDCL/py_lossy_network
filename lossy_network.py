import asyncio
import os
import sys
from datetime import datetime
from dataclasses import dataclass

import tabulate
import h5py
import numpy as np

from py_lossy_network import utils

@dataclass
class NetworkConfig:
    # ingress parameters
    ingress_bw: str = None
    ingress_burst: str = None

    # egress parameters
    egress_bw: str = None
    egress_burst: str = None
    egress_latency: str = None
    egress_loss: str = None
    egress_avg_delay: str = None
    egress_std_dev_delay: str = None


quit = False
network_interfaces = dict()


async def input_loop():
    global quit
    global network_interfaces

    # get the path to the h5 file and create the directory (if not already in existence)
    path_to_h5 = os.path.join(os.getcwd(), 'data')
    os.makedirs(path_to_h5, exist_ok=True)

    # come up with a name for the h5 file as the current date and time
    current_datetime = datetime.now()
    h5_file_name = (current_datetime.isoformat()).replace(':', '_').replace('-', '_').replace('.', '_')

    # create the h5 file
    h5_file = h5py.File(os.path.join(path_to_h5, h5_file_name + '.h5'), 'w')

    # create the datatypes we want to store in the h5 file
    vlen_str_dt = h5py.special_dtype(vlen=str)  # variable length strings
    vlen_np_float_dt = h5py.special_dtype(vlen=np.dtype('float64'))  # variable length numpy arrays (dtype=float)

    # create a dataset for client IP data
    client_ip_dset = h5_file.create_dataset(
        name='client_ip',
        shape=(0,),
        maxshape=(None,),
        dtype=vlen_str_dt
    )

    # create a dataset for bitrate data
    bitrate_dset = h5_file.create_dataset(
        name='bitrate_kbps',
        shape=(0,),
        maxshape=(None,),
        dtype=vlen_np_float_dt
    )

    # create a dataset for percent lost (UDP)
    percent_lost_udp_dset = h5_file.create_dataset(
        name='percent_lost_udp',
        shape=(0,),
        maxshape=(None,),
        dtype=float
    )

    # create a dataset for percent reordered (UDP)
    percent_reordered_udp_dset = h5_file.create_dataset(
        name='percent_reordered_udp',
        shape=(0,),
        maxshape=(None,),
        dtype=float
    )

    # create a dataset for percent lost (TCP)
    percent_lost_tcp_dset = h5_file.create_dataset(
        name='percent_lost_tcp',
        shape=(0,),
        maxshape=(None,),
        dtype=float
    )

    # create a dataset for delay in milliseconds
    delay_dset = h5_file.create_dataset(
        name='delay_ms',
        shape=(0,),
        maxshape=(None,),
        dtype=vlen_np_float_dt
    )

    # prompt the user with the "help" menu
    utils.prompt()

    # while the user hasn't quit, continue to prompt them
    while not quit:

        # asynchronously use the 'input' command, which is a blocking instruction
        user_input = await loop.run_in_executor(None, input, "> ")
        split_user_input = user_input.split(' ')

        # if user said 'quit', then quit
        if split_user_input[0] == 'quit':
            quit = True

        # if user said 'help', then prompt with help menu
        elif split_user_input[0] == 'help':
            utils.prompt()

        # if user said 'show', then
        elif split_user_input[0] == 'show':
            # the expected number of arguments is 2, so if it is not exactly 2, then prompt the user again
            if len(split_user_input) != 2:
                print("\"show\" command expects 1 argument, the name of the network interface. You provided {0} arguments".format(len(split_user_input) - 1))
                continue

            # get a list of the available network interfaces on this device
            network_interface_list = utils.list_available_interfaces()

            # if the user's input doesn't match one of those interfaces, then prompt the user again
            if not split_user_input[1] in network_interface_list:
                print("The network interface name you provided, \"{0}\" is invalid. Here is a list of valid network interface names: {1}".format(split_user_input[1], network_interface_list))
                continue

            # if the user's input is inside the network_interfaces object, then print it out
            if split_user_input[0] in network_interfaces:
                print(network_interfaces[split_user_input[0]])

            # if the user passed in a valid network interface, then we can look up the `tc` filters on that interface
            proc_tc_show = utils.show_tc_rules(split_user_input[1])

            # if the return code of the call to `tc` is not 0, that means the process failed, so just continue
            if proc_tc_show.returncode != 0:
                print(proc_tc_show.stderr.decode('utf-8'))
                continue

            # otherwise, print out the stdout
            print(proc_tc_show.stdout.decode('utf-8'))
        elif split_user_input[0] == 'del':
            # the expected number of arguments is 2, so if it is not exactly 2, then prompt the user again
            if len(split_user_input) != 2:
                print("\"del\" command expects 1 argument, the name of the network interface. You provided {0} arguments".format(len(split_user_input) - 1))
                continue

            # get a list of the available network interfaces on this device
            network_interface_list = utils.list_available_interfaces()

            # if the user's input doesn't match one of those interfaces, then prompt the user again
            if not split_user_input[1] in network_interface_list:
                print("The network interface name you provided, \"{0}\" is invalid. Here is a list of valid network interface names: {1}".format(split_user_input[1], network_interface_list))
                continue

            # if the user's input is inside the network_interfaces object, then delete it from there
            if split_user_input[1] in network_interfaces:
                network_interfaces.pop(split_user_input[1])

            # if the user passed in a valid network interface, then we can look up the `tc` filters on that interface
            proc_tc_del_root = utils.del_tc_rules(split_user_input[1], 'root')
            proc_tc_del_ingress = utils.del_tc_rules(split_user_input[1], 'ingress')

            # if the return code of the call to `tc` is not 0, that means the process failed, so just continue
            if proc_tc_del_root.returncode != 0 and proc_tc_del_ingress.returncode != 0:
                print(proc_tc_del_root.stderr.decode('utf-8'))
                print(proc_tc_del_ingress.stderr.decode('utf-8'))
                continue

            # if the return code of the call to `tc` is not 0, that means the process failed, so just continue

            # otherwise, print out the stdout
            print("Deleted successfully!")
            # print(proc_tc_del.stdout.decode('utf-8'))
        elif split_user_input[0] == 'set_egress':
            # the expected number of arguments is between 4 and 9.
            if len(split_user_input) != 13:
                print("\"set_egress\" command expects 12 arguments. You provided {0} arguments".format(len(split_user_input) - 1))
                continue

            # get a list of the available network interfaces on this device
            network_interface_list = utils.list_available_interfaces()

            # if the user's input doesn't match one of those interfaces, then prompt the user again
            if not split_user_input[1] in network_interface_list:
                print("The network interface name you provided, \"{0}\" is invalid. Here is a list of valid network interface names: {1}".format(split_user_input[1], network_interface_list))
                continue

            # extract the bandwidth, egress loss rate, and delay_ms passed in by the user
            egress_bw = None
            egress_burst = None
            egress_latency = None
            egress_loss = None
            egress_avg_delay = None
            egress_std_dev_delay = None
            for i in range(2, len(split_user_input)):
                if split_user_input[i] == 'bw':
                    # if 'egress_bw' is not 'none', then 'egress_bw' has already been assigned and the user passed in egress_loss twice
                    assert(egress_bw is None)

                    # make sure when we access split_user_input, there is enough space to accommodate i+1
                    assert(i+1 < len(split_user_input))

                    egress_bw = split_user_input[i+1]
                elif split_user_input[i] == 'loss':
                    # if 'egress_loss' is not 'none', then 'egress_loss' has already been assigned and the user passed in egress_bw twice
                    assert(egress_loss is None)

                    # make sure when we access split_user_input, there is enough space to accommodate i+1
                    assert(i+1 < len(split_user_input))

                    egress_loss = split_user_input[i+1]
                elif split_user_input[i] == 'burst':
                    # if 'egress_burst' is not 'none', then 'egress_burst' has already been assigned and the user passed in egress_burst twice
                    assert(egress_burst is None)

                    # make sure when we access split_user_input, there is enough space to accommodate i+1
                    assert(i+1 < len(split_user_input))

                    egress_burst = split_user_input[i+1]
                elif split_user_input[i] == 'latency':
                    # if 'egress_latency' is not 'none', then 'egress_latency' has already been assigned and the user passed in egress_latency twice
                    assert(egress_latency is None)

                    # make sure when we access split_user_input, there is enough space to accommodate i+1
                    assert(i+1 < len(split_user_input))

                    egress_latency = split_user_input[i+1]
                elif split_user_input[i] == 'delay':
                    # if 'delay_ms' variables are none; if they aren't this implies user assigned more than once
                    assert(egress_avg_delay is None and egress_std_dev_delay is None)

                    # make sure when we access split_user_input, there is enough space to accommodate i+2
                    assert(i+2 < len(split_user_input))
                    egress_avg_delay = split_user_input[i+1]
                    egress_std_dev_delay = split_user_input[i+2]

            if split_user_input[1] in network_interfaces:
                config = network_interfaces[split_user_input[1]]
            else:
                config = NetworkConfig()
            config.egress_bw = egress_bw
            config.egress_burst = egress_burst
            config.egress_latency = egress_latency
            config.egress_loss = egress_loss
            config.egress_avg_delay = egress_avg_delay
            config.egress_std_dev_delay = egress_std_dev_delay
            network_interfaces[split_user_input[1]] = config

            # add the rules
            utils.add_tbf_filter(split_user_input[1], 'root', '1:0', egress_bw, egress_burst, egress_latency)
            utils.add_netem_filter(split_user_input[1], 'parent 1:1', '10:0', egress_loss, egress_avg_delay, egress_std_dev_delay)
        elif split_user_input[0] == 'set_ingress':
            # the expected number of arguments is between 4 and 9.
            if len(split_user_input) != 6:
                print("\"set_ingress\" command expects 5 arguments. You provided {0} arguments".format(len(split_user_input) - 1))
                continue

            # get a list of the available network interfaces on this device
            network_interface_list = utils.list_available_interfaces()

            # if the user's input doesn't match one of those interfaces, then prompt the user again
            if not split_user_input[1] in network_interface_list:
                print("The network interface name you provided, \"{0}\" is invalid. Here is a list of valid network interface names: {1}".format(split_user_input[1], network_interface_list))
                continue

            # extract the bandwidth, egress loss rate, and delay_ms passed in by the user
            ingress_bw = None
            ingress_burst = None
            for i in range(2, len(split_user_input)):
                if split_user_input[i] == 'bw':
                    # if 'egress_bw' is not 'none', then 'egress_bw' has already been assigned and the user passed in egress_loss twice
                    assert(ingress_bw is None)

                    # make sure when we access split_user_input, there is enough space to accommodate i+1
                    assert(i+1 < len(split_user_input))

                    ingress_bw = split_user_input[i+1]
                elif split_user_input[i] == 'burst':
                    # if 'egress_burst' is not 'none', then 'egress_burst' has already been assigned and the user passed in egress_burst twice
                    assert(ingress_burst is None)

                    # make sure when we access split_user_input, there is enough space to accommodate i+1
                    assert(i+1 < len(split_user_input))

                    ingress_burst = split_user_input[i+1]

            if split_user_input[1] in network_interfaces:
                config = network_interfaces[split_user_input[1]]
            else:
                config = NetworkConfig()
            config.ingress_bw = ingress_bw
            config.ingress_burst = ingress_burst
            network_interfaces[split_user_input[1]] = config

            # add the rules
            utils.add_egress_rule(split_user_input[1], ingress_bw, ingress_burst)
        elif split_user_input[0] == 'sender':
            # the expected number of arguments is 2, so if it is not exactly 2, then prompt the user again
            if len(split_user_input) != 2:
                print("\"sender\" command expects 1 argument, the ip of the receiver. You provided {0} arguments".format(len(split_user_input) - 1))
                continue
            proc = utils.iperf3_client(split_user_input[1])
            if proc.returncode != 0:
                print(proc.stderr.decode('utf-8'))
                continue

            print("Success!")
        elif split_user_input[0] == 'receiver':
            # start iperf3 as the server (takes roughly 25 seconds)
            proc = utils.iperf3_server()

            # TODO: fix problem where timeout doesn't trigger retcode 0 causing us to skip this conditional
            if proc.returncode != 0:
                print(proc.stderr.decode('utf-8'))
                continue

            # extract relevant data from iperf3 output
            client_ip, bitrate_kbps, percent_lost_udp, percent_reordered_udp = utils.process_iperf3(proc.stdout.decode('utf-8'))

            # compute the delay (RTT egress_latency) & packet egress_loss (over TCP) by using `ping`; takes roughly 30 seconds
            proc = utils.ping(client_ip, count=20, timeout_seconds=120)

            # if `ping` crashed, then just continue (don't compute statistics)
            if proc.returncode != 0:
                print(proc.stderr.decode('utf-8'))
                continue

            # if `ping` did not crash, then extract delay measurements in milliseconds and the % packet egress_loss (over TCP)
            delay_ms, percent_lost_tcp = utils.process_ping(proc.stdout.decode('utf-8'))

            # save data to h5 file
            utils.save(client_ip_dset, client_ip)  # save the client's IP address (might be relevant)
            utils.save(bitrate_dset, bitrate_kbps)  # save all the bitrate measurements in kbps
            utils.save(percent_lost_udp_dset, percent_lost_udp)  # save the percent UDP packets lost
            utils.save(percent_reordered_udp_dset, percent_reordered_udp)  # save the percent UDP packets reordered
            utils.save(delay_dset, delay_ms)  # save the round-trip delay in milliseconds
            utils.save(percent_lost_tcp_dset, percent_lost_tcp)  # save the percent TCP packets lost

            # tables
            table = [
                ['client ip', 'avg. bitrate [kbit/s]', 'std. dev. bitrate [kbit/s]', '% udp lost', '% udp reordered', 'avg. delay [ms]', 'std. dev. delay [ms]', '% tcp lost'],
                [client_ip, round(np.mean(bitrate_kbps), 2), round(np.std(bitrate_kbps), 2), round(percent_lost_udp, 2), round(percent_reordered_udp, 2), round(np.mean(delay_ms), 2), round(np.std(delay_ms), 2), round(percent_lost_tcp, 2)]
            ]
            print(tabulate.tabulate(table, headers='firstrow', tablefmt='fancy_grid'))
    return 0


async def filtering_loop():
    global quit
    global network_interfaces

    while not quit:
        keys = list(network_interfaces.keys())
        # for k in keys:
        #     print(network_interfaces[k])
        await asyncio.sleep(1)


async def main():
    tasks = [input_loop(), filtering_loop()]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    sys.exit(loop.close())
