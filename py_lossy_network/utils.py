# standard library includes
import subprocess
import re
import asyncio

# external library includes
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
    Example: show eth0
del <INTERFACE>: 
    Description: deletes all `tc` filter rules on network interface <INTERFACE>
    Example: del eth0
set_egress <INTERFACE> bw <MEAN_BANDWIDTH> <STD_DEV_BANDWIDTH> burst <BURST> latency <LATENCY> loss <MEAN_LOSS> <STD_DEV_LOSS> delay <MEAN_DELAY> <STD_DEV_DELAY>
    Description: sets the egress bandwidth limit, burst limit, maximum latency, loss rate, and delay 
    Example: set_egress docker0 bw 500kbit 25kbit burst 32kbit latency 500ms loss 5% 0% delay 250ms 10ms
    Example: set_egress docker0 bw 25mbit 0kbit burst 64kbit latency 5s loss 0% 0% delay 0ms 0ms
    Example: set_egress docker0 bw 500kbit 25kbit burst 1mbit latency 250ms loss 0.5% 5% delay 10ms 50ms
set_ingress <INTERFACE> bw <MEAN_BANDWIDTH> <STD_DEV_BANDWIDTH> burst <BURST>
    Description: sets the ingress bandwidth limit and burst limit 
    Example: set_ingress docker0 bw 500kbit 10kbit burst 32kbit 
    Example: set_ingress docker0 bw 25mbit 0mbit burst 64kbit 
    Example: set_ingress docker0 bw 500kbit 1mbit burst 1mbit 
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
    :return:  a CompletedProcess object specifying success / failure of process
    """
    try:
        ret = subprocess.run(['tc', 'qdisc', 'show', 'dev', network_interface], capture_output=True)
    except:
        ret = subprocess.CompletedProcess(args="", returncode=1, stderr=b"failed", stdout=b"failed")
    return ret


def del_tc_rules(network_interface: str, qdisc: str) -> subprocess.CompletedProcess:
    """
    deletes `tc` queuing discipline rules on a particular network interface
    :param network_interface: the network interface which the queuing discipline applies to
    :param qdisc: the queuing discipline being deleted
    :return:  a CompletedProcess object specifying success / failure of process
    """
    bash_command = "sudo tc qdisc del dev {0} {1}".format(network_interface, qdisc)
    try:
        ret = subprocess.run(['bash', '-c', bash_command], capture_output=True)
    except:
        ret = subprocess.CompletedProcess(args="", returncode=1, stderr=b"failed", stdout=b"failed")
    return ret


def add_tbf_filter(network_interface: str, parent: str, handle: str, rate: str, burst: str,
                   latency: str) -> subprocess.CompletedProcess:
    """
    adds a `tbf` filter to a particular networking interface; that is, it introduces a maximum bound on egress bandwidth
    burst rate, and latency. That is, if a given network interface exceeds the stated maximum bandwidth limit, burst
    limit, or latency limit, then the rule will drop the corresponding datagrams or packets
    :param network_interface: the network interface to which we would like to apply the rule
    :param parent: the name of the parent node to this rule (see `tc` man pages for more information)
    :param handle: the name of the *this* rule (see `tc` man pages for more information)
    :param rate: the egress bandwidth limit
    :param burst: the egress bandwidth limit
    :param latency: the egress latency limit
    :return: a CompletedProcess object specifying success / failure of process
    """
    bash_command = "sudo tc qdisc add dev {0} {1} handle {2} tbf rate {3} burst {4} latency {5}".format(network_interface, parent, handle, rate, burst, latency)
    try:
        ret = subprocess.run(['bash', '-c', bash_command], capture_output=True)
    except:
        ret = subprocess.CompletedProcess(args="", returncode=1, stderr=b"failed", stdout=b"failed")
    return ret


def add_netem_filter(network_interface: str, parent: str, handle: str, loss: str, avg_delay: str,
                     std_dev_delay: str) -> subprocess.CompletedProcess:
    """
    adss a `netem` filter to a particular networking interface; that is, it introduces a constant loss rate, and an
    average and standard deviation delay to all egress traffic. In particular, all packets or datagrams eminating from
    this interface will get dropped at a constant rate (say 10%) and all traffic will get delayed according to a normal
    distribution parameterized by the stipulated mean and standard deviation
    :param network_interface: the network interface to which we would like to apply the rule
    :param parent: the name of the parent node to this rule (see `tc` man pages for more information)
    :param handle: the name of the *this* rule (see `tc` man pages for more information)
    :param loss: the egress loss rate
    :param avg_delay: the egress average delay
    :param std_dev_delay: the egress standard deviation delay
    :return:  a CompletedProcess object specifying success / failure of process
    """
    bash_command = "sudo tc qdisc add dev {0} {1} handle {2} netem loss {3} delay {4} {5} distribution normal ".format(network_interface, parent, handle, loss, avg_delay, std_dev_delay)
    try:
        ret = subprocess.run(['bash', '-c', bash_command], capture_output=True)
    except:
        ret = subprocess.CompletedProcess(args="", returncode=1, stderr=b"failed", stdout=b"failed")
    return ret


def add_ingress_rule(network_interface: str, bw: str, burst: str) -> subprocess.CompletedProcess:
    """
    adds a couple of `tc` rules to limit the ingress bandwidth and burst rates
    :param network_interface: the network interface to which we would like to apply the rule
    :param bw: the ingress bandwidth limit
    :param burst: the ingress burst rate limit
    :return:  a CompletedProcess object specifying success / failure of process
    """
    bash_command = "sudo tc qdisc add dev {0} handle ffff: ingress && " \
                   "sudo tc filter add dev {0} parent ffff: u32 match u32 0 0 police rate {1} burst {2}".format(network_interface, bw, burst)
    try:
        ret = subprocess.run(['bash', '-c', bash_command], capture_output=True)
    except:
        ret = subprocess.CompletedProcess(args="", returncode=1, stdout=b"failed", stderr=b"failed")
    return ret


async def ping(ip_addr: str, count: int = 10) -> subprocess.CompletedProcess:
    """
    this function performs a `ping` test targeted at the stipulated IP address for the purpose of measuring the delay
    and tcp packet loss over the given network interface
    :param ip_addr: the ip address of the target machine
    :param count: the number of times we will ping the target machine
    :return: a CompletedProcess object specifying success / failure of process
    """
    try:
        bash_command = 'ping -c {0} {1}'.format(count, ip_addr)
        proc = await asyncio.create_subprocess_shell(bash_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        ret = subprocess.CompletedProcess(args="", returncode=0, stdout=stdout, stderr=stderr)
    except:
        ret = subprocess.CompletedProcess(args="", returncode=1, stdout=b"failed", stderr=b"failed")
    return ret


async def iperf3_server() -> subprocess.CompletedProcess:
    """
    this function creates an iperf3 server process for the purpose of measuring the UDP bandwidth, UDP datagram loss
    rate, and UDP datagram reordering rate
    :return:  a CompletedProcess object specifying success / failure of process
    """
    try:
        bash_command = 'iperf3 -s -1'
        proc = await asyncio.create_subprocess_shell(bash_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        ret = subprocess.CompletedProcess(args="", returncode=0, stdout=stdout, stderr=stderr)
    except:
        ret = subprocess.CompletedProcess(args="", returncode=1, stdout=b"failed", stderr=b"failed")
    return ret


async def iperf3_client(receiver_ip_addr: str) -> subprocess.CompletedProcess:
    """
    this function creates an iperf3 client process targeted at the given ip address for the purpose of measuring the UDP
    bandwidth, UDP datagram loss rate, and the UDP datagram reordering rate
    :param receiver_ip_addr: the ip address of the iperf3 server
    :return: a CompletedProcess object specifying success / failure of process
    """
    try:
        bash_command = 'iperf3 -c {0} -u -b 95M'.format(receiver_ip_addr)
        proc = await asyncio.create_subprocess_shell(bash_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        ret = subprocess.CompletedProcess(args="", returncode=0, stdout=stdout, stderr=stderr)
    except:
        ret = subprocess.CompletedProcess(args="", returncode=1, stdout=b"failed", stderr=b"failed")
    return ret


def list_available_interfaces() -> list:
    """
    gets a list of strings denoting the network interfaces of this machine
    :return:
    """
    try:
        proc_ifconfig = subprocess.run(['ifconfig', '-a'], check=True, capture_output=True)
    except:
        return []

    try:
        network_interface_list = subprocess.run(['sed', 's/[ \t].*//;/^$/d'], input=proc_ifconfig.stdout,capture_output=True).stdout.decode('utf-8').split(':\n')
    except:
        return []
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
    bitrates_regex = re.compile('\d+.\d+ [a-zA-Z]*bits\/sec')
    bitrates = bitrates_regex.findall(iperf3_output)[:-1]  # vector of strings containing datarate with unit

    # transform the vector of strings into numpy vector with assumed units of kilobits per second
    bitrate_kbps = np.zeros((len(bitrates),))
    for i in range(0, len(bitrates)):
        # iperf3 outputs kbits as Kbits (which isn't technically correct, it should be 'kbits'). so we check for that
        # case before handing off to `pint` to transform the units.
        if bitrates[i][-9] == 'K':
            bitrates[i] = bitrates[i].lower()
        bitrates[i] = ureg(bitrates[i]).to(ureg.kbit / ureg.s)  # perform unit conversion
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

    # To get the ratio of lost datagrams and reordered datagrams, we need to divide by the total datagrams. However, if
    # iperf3 fails for any reason (like client disconnects from the server in the middle of the test), then we won't
    # see ANY datagrams on the server side. Therefore, it is necessary to check for the condition that we don't get
    # any datagrams BEFORE we divide by total datagrams to avoid a division by zero error.
    lost_datagram_ratio = 0.0
    reordered_datagram_ratio = 0.0
    if total_datagrams == 0:
        # in this case we the ratio is NaN and we can infer that some iperf3 error occurred
        lost_datagram_ratio = float('nan')
        reordered_datagram_ratio = float('nan')
    else:
        lost_datagram_ratio = float(lost_datagrams / total_datagrams)
        reordered_datagram_ratio = float(reordered_datagrams / total_datagrams)

    return client_ip, bitrate_kbps, lost_datagram_ratio, reordered_datagram_ratio


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
    percent_packet_loss = float(packet_loss_regex.findall(ping_output)[0][:-1]) / 100.  # divide by 100, since nominally in form: X%

    return delay_ms, percent_packet_loss


def save(dset, data):
    dset.resize(dset.shape[0]+1, axis=0)
    dset[-1] = data
