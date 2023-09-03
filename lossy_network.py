import os
import sys

import numpy as np

from py_lossy_network import utils
import re
import h5py
from datetime import datetime


def main() -> int:
    """

    :return: return code for program
    """

    # get the path to the h5 file and create the directory (if not already in existence)
    path_to_h5 = os.path.join(os.getcwd(), 'data')  # get path to h5 file
    os.makedirs(path_to_h5, exist_ok=True)  # create the directory

    # determine the name of the file
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

    while True:
        user_input = input("")
        split_user_input = user_input.split(' ')
        if split_user_input[0] == 'quit':
            break
        elif split_user_input[0] == 'help':
            utils.prompt()
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

            # if the user passed in a valid network interface, then we can look up the `tc` filters on that interface
            proc_tc_del = utils.del_tc_rules(split_user_input[1])

            # if the return code of the call to `tc` is not 0, that means the process failed, so just continue
            if proc_tc_del.returncode != 0:
                print(proc_tc_del.stderr.decode('utf-8'))
                continue

            # otherwise, print out the stdout
            print(proc_tc_del.stdout.decode('utf-8'))
        elif split_user_input[0] == 'set':
            # the expected number of arguments is between 4 and 9.
            if len(split_user_input) != 13:
                print("\"set\" command expects 12 arguments. You provided {0} arguments".format(len(split_user_input) - 1))
                continue

            # get a list of the available network interfaces on this device
            network_interface_list = utils.list_available_interfaces()

            # if the user's input doesn't match one of those interfaces, then prompt the user again
            if not split_user_input[1] in network_interface_list:
                print("The network interface name you provided, \"{0}\" is invalid. Here is a list of valid network interface names: {1}".format(split_user_input[1], network_interface_list))
                continue

            # extract the bandwidth, loss rate, and delay_ms passed in by the user
            bw = None
            burst = None
            latency = None
            loss = None
            avg_delay = None
            std_dev_delay = None
            for i in range(2, len(split_user_input)):
                if split_user_input[i] == 'bw':
                    # if 'bw' is not 'none', then 'bw' has already been assigned and the user passed in loss twice
                    assert(bw is None)

                    # make sure when we access split_user_input, there is enough space to accommodate i+1
                    assert(i+1 < len(split_user_input))

                    bw = split_user_input[i+1]
                elif split_user_input[i] == 'loss':
                    # if 'loss' is not 'none', then 'loss' has already been assigned and the user passed in bw twice
                    assert(loss is None)

                    # make sure when we access split_user_input, there is enough space to accommodate i+1
                    assert(i+1 < len(split_user_input))

                    loss = split_user_input[i+1]
                elif split_user_input[i] == 'burst':
                    # if 'burst' is not 'none', then 'burst' has already been assigned and the user passed in burst twice
                    assert(burst is None)

                    # make sure when we access split_user_input, there is enough space to accommodate i+1
                    assert(i+1 < len(split_user_input))

                    burst = split_user_input[i+1]
                elif split_user_input[i] == 'latency':
                    # if 'latency' is not 'none', then 'latency' has already been assigned and the user passed in latency twice
                    assert(latency is None)

                    # make sure when we access split_user_input, there is enough space to accommodate i+1
                    assert(i+1 < len(split_user_input))

                    latency = split_user_input[i+1]
                elif split_user_input[i] == 'delay':
                    # if 'delay_ms' variables are none; if they aren't this implies user assigned more than once
                    assert(avg_delay is None and std_dev_delay is None)

                    # make sure when we access split_user_input, there is enough space to accommodate i+2
                    assert(i+2 < len(split_user_input))
                    avg_delay = split_user_input[i+1]
                    std_dev_delay = split_user_input[i+2]

            # add the rules
            utils.add_tbf_filter(split_user_input[1], 'root', '1:0', bw, burst, latency)
            utils.add_netem_filter(split_user_input[1], 'parent 1:1', '10:0', loss, avg_delay, std_dev_delay)
        elif split_user_input[0] == 'sender':
            # the expected number of arguments is 2, so if it is not exactly 2, then prompt the user again
            if len(split_user_input) != 2:
                print("\"sender\" command expects 1 argument, the ip of the receiver. You provided {0} arguments".format(len(split_user_input) - 1))
                continue
            proc = utils.iperf3_client(split_user_input[1])
            if proc.returncode != 0:
                print(proc.stderr.decode('utf-8'))
                continue
            print(proc.stdout.decode('utf-8'))
        elif split_user_input[0] == 'receiver':
            # start iperf3 as the server (takes roughly 25 seconds)
            proc = utils.iperf3_server()

            # TODO: fix problem where timeout doesn't trigger retcode 0 causing us to skip this conditional
            if proc.returncode != 0:
                print(proc.stderr.decode('utf-8'))
                continue

            # extract relevant data from iperf3 output
            client_ip, bitrate_kbps, percent_lost_udp, percent_reordered_udp = utils.process_iperf3(proc.stdout.decode('utf-8'))

            # compute the delay (RTT latency) & packet loss (over TCP) by using `ping`; takes roughly 30 seconds
            proc = utils.ping(client_ip, count=30, timeout_seconds=120)

            # if `ping` crashed, then just continue (don't compute statistics)
            if proc.returncode != 0:
                print(proc.stderr.decode('utf-8'))
                continue

            # if `ping` did not crash, then extract delay measurements in milliseconds and the % packet loss (over TCP)
            delay_ms, percent_lost_tcp = utils.process_ping(proc.stdout.decode('utf-8'))

            # save data to h5 file
            utils.save(client_ip_dset, client_ip)  # save the client's IP address (might be relevant)
            utils.save(bitrate_dset, bitrate_kbps)  # save all the bitrate measurements in kbps
            utils.save(percent_lost_udp_dset, percent_lost_udp)  # save the percent UDP packets lost
            utils.save(percent_reordered_udp_dset, percent_reordered_udp)  # save the percent UDP packets reordered
            utils.save(delay_dset, delay_ms)  # save the round-trip delay in milliseconds
            utils.save(percent_lost_tcp_dset, percent_lost_tcp)  # save the percent TCP packets lost
    return 0


if __name__ == '__main__':
    sys.exit(main())
