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
2. Simulate a lossy network between multiple docker containers on the same host machine by interfering with the standard 
docker's virtual network interfaces.
3. Stress test an actual network of devices (such as between robots and a ground station) by limiting ingress bandwidth 
at the ground station. This is useful if you don't want to modify or cannot modify the robot's code to add this software
package. You can simply run this code on the ground station and see what happens to the performance of the system when 
subjected to lossy network conditions.
4. Stress test an actual network of devices (such as between robots and a ground station) by limiting egress bandwidth, 
delay, and loss rate from the robots. This is useful if you want to simulate very specific or particularly severe 
network conditions.   

## Usage
Install `tc`, `iperf3`, and `ping`.

### Debian Linux (such as Ubuntu)
```bash
sudo apt install -y iproute2 iperf3 net-tools iputils-ping
```


## Terms
1. Bandwidth: the number of bits per second a given network connection can handle.
2. Ingress/Egress Traffic: Ingress traffic is incoming traffic. Ingress traffic is all the information a given network 
interface is receiving. Ingress bandwidth is like "download speed". Egress traffic is outgoing traffic. Egress traffic 
is all the information a given interface is sending. Egress bandwidth is like "upload speed"  
3. Loss Rate: The percentage of packets or datagrams dropped. 
4. Delay: Sometimes called "latency". This is the time it takes a packet to leave a network interface on the 
transmitting device and enter the network interface on the receiving device.