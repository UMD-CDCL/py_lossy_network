import h5py
import numpy as np
import matplotlib.pyplot as plt



# Example: path = '/home/zach/Documents/spot/py_lossy_network/data/2023_09_12T14_20_04_943741.h5'
path = ''
assert(path != '')

f = h5py.File(path, 'r')
print(f.keys())
keys = [
    'bitrate_kbps', 'delay_ms', 'percent_lost_tcp'
]

d = dict()
for k in keys:
    d[k] = np.array([])
    for i in range(0, f[k].shape[0]):
        if type(f[k][i]) == np.float64:
            d[k] = np.append(d[k], f[k][i])
        else:
            d[k] = np.concatenate((d[k], f[k][i]))

    print("{0}: mean: {1} std. dev.: {2}".format(k, np.mean(d[k]), np.std(d[k])))

# plot bandwidth
num_bins = 25
plt.grid(linestyle='--', linewidth=0.5)
plt.hist(d['bitrate_kbps'].ravel(), bins=np.linspace(np.min(d['bitrate_kbps']), np.max(d['bitrate_kbps']), num=num_bins)) #<-- Change here.  Note the use of ravel.
plt.title("histogram of bandwidth tests")
plt.xlabel("bandwidth [kbit/s]")
plt.ylabel("# occurrences")
plt.show()

# plot delay
num_bins = 25  # i like 50 and 25
plt.grid(linestyle='--', linewidth=0.5)
plt.hist(d['delay_ms'].ravel(), bins=np.linspace(np.min(d['delay_ms']), np.max(d['delay_ms']), num=num_bins)) #<-- Change here.  Note the use of ravel.
plt.title("histogram of network delay")
plt.xlabel("network delays [ms]")
plt.ylabel("# occurrences")
plt.show()

# % Lost TCP packets
num_bins = 25  # i like 50 and 25
plt.grid(linestyle='--', linewidth=0.5)
plt.hist(d['delay_ms'] .ravel(), bins=np.linspace(0, 1.0, num=num_bins)) #<-- Change here.  Note the use of ravel.
plt.title("histogram of packets dropped")
plt.xlabel("fraction of packets dropped")
plt.ylabel("# occurrences")
plt.show()