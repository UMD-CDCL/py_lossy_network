import subprocess
import re
import numpy as np
from pint import UnitRegistry


def prompt():
    prompt = """
List of Available Commands:
quit: 
    Description: quits program
help: 
    Description: shows list of commands
show <INTERFACE>: 
    Description: shows all `tc` filter rules on network interface <INTERFACE>
    Example: "show eth0"
del <INTERFACE>: 
    Description: deletes all `tc` filter rules on network interface <INTERFACE>
    Example: del eth0
set <INTERFACE> bw <BANDWIDTH> burst <BURST> latency <LATENCY> loss <LOSS> delay <MEAN_DELAY> <STD_DEV_DELAY>
    Description: sets the outgoing (upload) bandwidth limit, burst limit, and latency limit 
    Example: set docker0 bw 500kbit burst 32kbit latency 500ms loss 5% delay 250ms 10ms
    Example: set docker0 bw 25mbit burst 64kbit latency 5s loss 0% delay 0ms 0ms
    Example: set docker0 bw 500kbit burst 1mbit latency 250ms loss 0.5% delay 10ms 50ms
"sender <SERVER_IP>": 
    Description: initiates data collection with the host system as the sender of data
    Example: sender 172.17.0.2
"receiver":
    Description: initiates data collection with the host system as the receiver of data
    Example: receiver
        """
    print(prompt)


def show_tc_rules(network_interface: str) -> subprocess.CompletedProcess:
    """
    displays the filter rules applied by `tc` on a particular network interface
    :param network_interface: the network interface we would like to display filter rules for represented as a str
    :return: the output of the call to `tc`
    """
    return subprocess.run(['tc', 'qdisc', 'show', 'dev', network_interface], capture_output=True)


def del_tc_rules(network_interface: str) -> subprocess.CompletedProcess:
    """

    :param network_interface:
    :return:
    """
    bash_command = "sudo tc qdisc del dev {0} root".format(network_interface)
    return subprocess.run(['bash', '-c', bash_command], capture_output=True)


def add_tbf_filter(network_interface: str, parent: str, handle: str, rate: str, burst: str,
                   latency: str) -> subprocess.CompletedProcess:
    """

    :param network_interface:
    :param parent:
    :param handle:
    :param rate:
    :param burst:
    :param latency:
    :return:
    """
    bash_command = "sudo tc qdisc add dev {0} {1} handle {2} tbf rate {3} burst {4} latency {5}".format(
        network_interface, parent, handle, rate, burst, latency)
    return subprocess.run(['bash', '-c', bash_command], capture_output=True)


def add_netem_filter(network_interface: str, parent: str, handle: str, loss: str, avg_delay: str,
                     std_dev_delay: str) -> subprocess.CompletedProcess:
    """

    :param network_interface:
    :param parent:
    :param handle:
    :param loss:
    :param avg_delay:
    :param std_dev_delay:
    :return:
    """
    bash_command = "sudo tc qdisc add dev {0} {1} handle {2} netem loss {3} delay {4} {5} distribution normal ".format(
        network_interface, parent, handle, loss, avg_delay, std_dev_delay)
    return subprocess.run(['bash', '-c', bash_command], capture_output=True)


def ping(ip_addr: str, count: int = 10, timeout_seconds: int = 20) -> subprocess.CompletedProcess:
    """

    :param ip_addr:
    :param count:
    :param timeout_seconds:
    :return:
    """
    return subprocess.run(['ping', '-c', str(count), ip_addr], capture_output=True, timeout=timeout_seconds)


def iperf3_server(timeout_seconds: int = 120) -> subprocess.CompletedProcess:
    """

    :return:
    """
    return subprocess.run(['iperf3', '-s', '-1'], capture_output=True, timeout=timeout_seconds)


def iperf3_client(receiver_ip_addr: str, timeout_seconds: int = 120) -> subprocess.CompletedProcess:
    """

    :param receiver_ip_addr:
    :return:
    """
    return subprocess.run(['iperf3', '-c', receiver_ip_addr, '-u'], capture_output=True, timeout=timeout_seconds)


def list_available_interfaces() -> list:
    """

    :return:
    """
    proc_ifconfig = subprocess.run(['ifconfig', '-a'], check=True, capture_output=True)
    network_interface_list = subprocess.run(['sed', 's/[ \t].*//;/^$/d'], input=proc_ifconfig.stdout,
                                            capture_output=True).stdout.decode('utf-8').split(':\n')
    return [interface for interface in network_interface_list if interface != '']


def process_iperf3(iperf3_output: str):
    """
    process the server-side output of iperf3 in udp mode, extracting: the client's IP address, bandwidth measurements,
    percent datagrams lost, and the percent datagrams reordered
    :param iperf3_output: the server-side output of running iperf3 in udp mode
    :return: the clients IP as a string, a numpy vector of bandwidth measurements in kbps, percent datagrams lost, and
    the percent datagrams reordered
    """
    # Instantiate a "pint" (python package) unit registry object for handling iperf's units (which may be variable)
    ureg = UnitRegistry()

    # Use regex to ascertain the client's IP address
    client_ip_regex = re.compile('Accepted connection from \d+.\d+.\d+.\d+')  # regular expression for getting IP
    client_ip = client_ip_regex.findall(iperf3_output)[0].split(' ')[-1]  # some processing of the matched string

    # Use regex to ascertain all datarate measurements
    bitrates_regex = re.compile('\d+.\d+ [a-zA-Z]bits\/sec')
    bitrates = bitrates_regex.findall(iperf3_output)[:-1]  # vector of strings containing datarate with unit

    # transform the vector of strings into numpy vector with assumed units of kilobits per second
    bitrate_kbps = np.zeros((len(bitrates),))
    for i in range(0, len(bitrates)):
        bitrates[i] = ureg(bitrates[i].lower()).to(ureg.kbit / ureg.s)  # perform unit conversion
        bitrate_kbps[i] = bitrates[i].m  # get the value of the "Quantity" object (not the unit)

    # get number of lost datagrams and  total number of datagrams
    datagrams_regex = re.compile('\d+\/\d+')
    datagrams = datagrams_regex.findall(iperf3_output)[-1].split('/')
    lost_datagrams = int(datagrams[0])
    total_datagrams = int(datagrams[1])

    # number of out-of-order datagrams
    reordered_regex = re.compile('\d+ datagrams')
    reordered_regex_match = reordered_regex.findall(iperf3_output)

    # if nothing gets reordered, it's possible nothing gets printed, and we don't match anything, so check for that
    if len(reordered_regex_match) > 0:
        reordered_datagrams = int(reordered_regex.findall(iperf3_output)[0].split(' ')[0])
    else:
        reordered_datagrams = 0

    return client_ip, bitrate_kbps, float(lost_datagrams / total_datagrams), float(
        reordered_datagrams / total_datagrams)


def process_ping(ping_output: str):
    """
    process the output of 'ping', extracting: delay measurements and the percent packet loss
    :param ping_output: the output of running `ping` represented as a string
    :return: delay measurements as a numpy array with units of milliseconds and the percent packet loss
    """
    # Instantiate a "pint" (python package) unit registry object for handling iperf's units (which may be variable)
    ureg = UnitRegistry()

    # use regex to extract all delays (with units) in form of strings
    delay_regex = re.compile('\d+.\d+ [a-zA-Z]s')
    delays = delay_regex.findall(ping_output)

    # transform the list of strings into a numpy array of floats with assumed units of milliseconds
    delay_ms = np.zeros((len(delays),))
    for i in range(0, len(delays)):
        delay = ureg(delays[i]).to(ureg.ms)  # perform the unit transformation
        delay_ms[i] = delay.m  # save the value of the "Quantity" object, not the unit

    # find packet loss
    packet_loss_regex = re.compile('[\d+.\d+]%')
    print(packet_loss_regex.findall(ping_output)[0])
    percent_packet_loss = float(packet_loss_regex.findall(ping_output)[0][:-1]) / 100.  # divide by 100, since nominally in form: X%

    return delay_ms, percent_packet_loss


def save(dset, data):
    dset.resize(dset.shape[0]+1, axis=0)
    dset[-1] = data
    print("Dset:\n shape: {0}\n last element: {1}".format(dset.shape[0], dset[-1]))