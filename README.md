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
