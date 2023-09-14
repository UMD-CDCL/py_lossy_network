> this documentation is incomplete. Reach out to @zborffs for questions.

# Overview
This is a Python package for (1) simulating and (2) testing the performance of lossy networks. 

Specifically, this package can do the following:
1. Enforce a network interface on machine to have a set (average/standard deviation) (ingress/egress) bandwidth.
2. Enforce a network interface on machine to have a set (average/standard deviation) egress loss rate.
3. Enforce a network interface on machine to have a set (average/standard deviation) egress delay.
4. Determine a target network connection's bandwidth, latency, loss rate, and reordering rate. 

## Use Cases
1. Simulate a lossy network between ROS1/2 nodes on the same host machine by interfering with whatever interface ROS1/2 
is using (based on your system setup).
2. Simulate a lossy network between multiple docker containers on the same host machine by interfering with docker's 
virtual network interfaces.
3. Stress test an actual network of devices (such as between robots and a ground station) by limiting ingress bandwidth 
at the ground station. This is useful if you don't want to modify or cannot modify the robot's code to add this software
package. You can simply run this code on the ground station and see what happens to the performance of the system when 
subjected to lossy network conditions.
4. Stress test an actual network of devices (such as between robots and a ground station) by limiting egress bandwidth, 
delay, and loss rate from the robots. This is useful if you want to simulate very specific or particularly severe 
network conditions.   

## Usage
### Installation
Install `tc`, `iperf3`, and `ping`.

#### Debian Linux (such as Ubuntu)
```bash
sudo apt install -y iproute2 iperf3 net-tools iputils-ping
```

#### Clone this Repo (must have access)
Clone the most recent commit from the `main` branch to get the latest stable release!
```bash
git clone git@github.com:UMD-CDCL/py_lossy_network.git
```

#### Install the `python` Dependencies
Install `pip`. Then run
```bash
cd py_lossy_network
pip3 install -r requirements.txt  # if pip maps to python3, then run "pip install -r requirements.txt"
```

### Running the Code
To run the main program, just run:
```bash
python3 lossy_network.py
```

You should see the following prompt:
```bash
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
set_egress <INTERFACE> bw <MEAN_BANDWIDTH> <STD_DEV_BANDWIDTH> burst <BURST> latency <LATENCY> loss <MEAN_LOSS> <STD_DEV_LOSS> delay <MEAN_DELAY> <STD_DEV_DELAY>
    Description: sets the egress bandwidth limit, burst limit, and latency limit 
    Example: set_egress docker0 bw 500kbit 25kbit burst 32kbit latency 500ms loss 5% 0% delay 250ms 10ms
    Example: set_egress docker0 bw 25mbit 0kbit burst 64kbit latency 5s loss 0% 0% delay 0ms 0ms
    Example: set_egress docker0 bw 500kbit 25kbit burst 1mbit latency 250ms loss 0.5% 5% delay 10ms 50ms
set_ingress <INTERFACE> bw <MEAN_BANDWIDTH> <STD_DEV_BANDWIDTH> burst <BURST>
    Description: sets the egress bandwidth limit and burst limit 
    Example: set_ingress docker0 bw 500kbit burst 32kbit 
    Example: set_ingress docker0 bw 25mbit burst 64kbit 
    Example: set_ingress docker0 bw 500kbit burst 1mbit 
"sender <SERVER_IP>": 
    Description: initiates data collection with the host system as the sender of data
    Example: sender 172.17.0.2
"receiver":
    Description: initiates data collection with the host system as the receiver of data
    Example: receiver
        
> 
```

## Terms
1. Bandwidth: the number of bits per second a given network connection can "handle" without the network saturating.
2. Ingress/Egress Traffic: Ingress traffic is incoming traffic. Ingress traffic is all the information a given network 
interface on a machine is receiving. Egress traffic is outgoing traffic. Egress traffic 
is all the information a given interface is sending. 
3. Ingress/Egress Bandwidth: Ingress bandwidth is like "download speed". Egress bandwidth is like "upload speed".  
4. Loss Rate: The percentage of packets or datagrams dropped. 
5. Delay: Sometimes called "latency" (though the "latency" parameter in this tool means something else). This is the 
time it takes a packet to leave a network interface on the transmitting device and enter the network interface on the 
receiving device.

## References
1. [`iperf3` Documentation](https://iperf.fr/iperf-doc.php)
    - `iperf3` is an amazing tool. look through the docs and see what it can do!
2. [`iperf` tutorial](http://openmaniak.com/iperf.php)
    - outdated reference. but it explains how `iperf` and `iperf3` "work" and how it should be complemented by other 
    tools to get a more holistic picture of network health.
3. [`iperf3` video tutorial](https://www.youtube.com/watch?v=0MEBoPwoqKE)
    - good explainer. follow along and learn some useful commands!
4. [`sar` Documentation](https://linux.die.net/man/1/sar)
    - `sar` is not actively being used by this tool, but maybe one day it will. it can be used to monitor network 
    interface stats upstream from the `tc` rules.
5. [`sar` Examples](https://medium.com/@malith.jayasinghe/network-monitoring-using-sar-37bab6ce9f68)
    - see how this guy is using `sar`. i found this to be more clear than the official documentation for `sar`.
6. [`tc` Documentation](https://www.man7.org/linux/man-pages/man8/tc.8.html)
    - documentation for `tc`, the tool that *THIS* tool is built on. It is a thorough and clear document. Must read! 
7. [`tc-tbf` Documentation](https://www.man7.org/linux/man-pages/man8/tc-tbf.8.html)
    - documentation for `tc-tbf`
8. [`tc-police` Documentation](https://www.man7.org/linux/man-pages/man8/tc-police.8.html)
    - documentation for `tc-police`
9. [`tc-netem` Documentation](https://www.man7.org/linux/man-pages/man8/tc-netem.8.html)
    - documentation for `tc-netem`
10. [`tc` examples](https://serverfault.com/questions/583788/implementing-htb-netem-and-tbf-traffic-control-simultaneously)
    - see a few examples of how to use `tc` to shape network traffic
11. [`tc` fundamentals video](https://www.youtube.com/watch?v=Qd7KMewRvNQ)
    - this guy explains fundamental concepts of `tc` and how it works
12. [`docker` compatibility](https://github.com/ahervieu/Docker-Cgroup-Doc)
    - want to use this tool in a docker container? Well follow this tutorial to find out how! 