import sys, os
import paramiko
import socket
import getpass
import pickle


class cabinet():

    def __init__(self, number):
        fail = "failure{0}.txt".format(number)
        passing = "success{0}.txt".format(number)
        if os.path.isfile(fail):
            os.remove(fail)
        if os.path.isfile(passing):
            os.remove(passing)
        self.success = open(passing, 'a')
        self.failure = open(fail, 'a')

    def pingable(self, router_ip):
        self.success.write(router_ip + '\n')

    def unpingable(self, router_ip, reason):
        result = str(router_ip + " " + reason)
        self.failure.write(result)

    def closure(self):
        self.success.close()
        self.failure.close()


def deviplist(): #used to create a dict from a large item list
    subips = {}
    f = open("IP-List.txt", "r")
    primeip = f.read().splitlines()
    i = 1 #prime key index
    group = [] #empty sub list
    while len(primeip) >= 100:
        for j in range(0, 99):
            group.append(primeip.pop()) #pop from sub list and add to group
        subips[str(i)] = group #attach group to dict key
        i += 1 #increment key index
        group = [] #clear group list for new dict value
    for j in range(0, len(primeip)): #used to add remaining items when list is below 100
        group.append(primeip.pop())
    subips[str(i)] = group
    pklfile = open('ip-dictionary.pkl', 'wb')
    pickle.dump(subips, pklfile) #serialize dict data to a file
    pklfile.close()
    return subips


def main():
    if not (os.path.isfile("ip-dictionary.pkl")) and os.path.isfile("IP-List.txt"): #if dict file not available, create
        subips = deviplist()
    elif os.path.isfile("ip-dictionary.pkl"): #if dict file available, recover
        pklfile = open('ip-dictionary.pkl', 'rb')
        subips = pickle.load(pklfile)
        pklfile.close()
    else:
        print("Need \"IP-List.txt\" file to proceed.") #failover if neither file is available
        exit()

    user = raw_input("Type username:")
    password = getpass.getpass()
    item = raw_input("Type item number from 1 to {0}:".format(len(subips)))

    filing = cabinet(item)
    ip_list = subips[item]
    i = 0
    for device in ip_list:
        try: #attempt connection
            i += 1
            print(i)
            remote = paramiko.SSHClient()
            remote.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            remote.connect(hostname=device, port=22, username=user, password=password, timeout=10)
        except socket.gaierror:
            # print('Could not connect to {0}'.format(device))
            filing.unpingable(device, "Connection failed \n")
        except paramiko.AuthenticationException:
            # print('Could not authenticate to {0} \n'.format(device))
            filing.unpingable(device, "Authentication failure \n")
        except socket.error:
            # print('Connection Timed out: {0} \n'.format(device))
            filing.unpingable(device, "Connection Timed out \n")
        except paramiko.SSHException:
            # print('Incompatible ssh peer: {0} \n'.format(device))
            filing.unpingable(device, "Incompatible ssh peer \n")
        except Exception:
            # print("Unexpected error")
            filing.unpingable(device, "Unknown error")
        else:
            filing.pingable(device)
        finally:
            remote.close() #close device connection
    filing.closure() #close respective success and failure files


if __name__ == '__main__':
    """Python interpreter check"""
    try:
        assert sys.version_info[0] < 3
    except AssertionError:
        print("Incorrect interpreter being run. Please use Python 2.x")
        exit()
    main()

