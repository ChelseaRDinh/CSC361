import sys
import socket
import dpkt
from dpkt.udp import UDP
import datetime
import numpy

class datagram:
    gram_id = 0
    last_offset = 0
    num_fragments = 0
    frag_times = []
    time_rcv = 0
    seq_num = 0
    proto = ""
    src_p = 0
    dst_ip = ""
    ttl = 0
    def __init__(self, gram_id, last_offset, num_fragments):
        self.gram_id = gram_id
        self.last_offset = last_offset
        self.num_fragments = num_fragments
        self.frag_times = []
        self.time_rcv = 0
        self.seq_num = 0
        self.proto = ""
        self.src_p = 0
        self.dest_ip = ""
        self.ttl = 0
    def create_datagram(gram_id, last_offset, num_fragments):
        d = create_datagram(gram_id, last_offset, num_fragments)
        return d

#Calculate relative time from time deltas of capture file
def relative_time(time_list):
    times = []
    prev_time = time_list[0]
    for time in time_list:
        time_diff = time-prev_time
        prev_time = time
        times.append(time_diff)
    value = 0
    for new_time in times:
        value = value+new_time.total_seconds()
    return value

#Convert inet object to readable ip address in string format
def compute_ip_address(inet):
    # First try ipv4 and then ipv6
    try:
        return socket.inet_ntop(socket.AF_INET, inet)
    except ValueError:
        return socket.inet_ntop(socket.AF_INET6, inet)

def find_datagram(d, datagrams):
    index = 0
    for gram in datagrams:
        if gram.gram_id == d.gram_id:
            return index
        index = index+1
    return None

def calculate_rtts(datagrams, error_msgs, file_type, src_node_ip, dst_ip):
    routers = []
    #create list of router ips and frag times
    for msg in error_msgs:
        router = {'ip': msg['ip'], 'times': []}
        if routers.count(router) == 0:
            routers.append(router)
    #Check file type and calculate avg rtts accordingly
    for d in datagrams:
        #If file type is linux, match src port of UDP with src port of icmp error msg
        if file_type == 'LINUX':
            for msg in error_msgs:
                if d.src_p == msg['src_port']:
                    frag_rtt = float(msg['time_rcv']-d.time_rcv)*1000
                    for router in routers:
                        if router['ip'] == msg['ip']:
                            router['times'].append(frag_rtt)
        #If file type is win, match sequence num of ICMP echo msg with sequence num of icmp error msg
        elif file_type == 'WIN':
            for msg in error_msgs:
                if d.seq_num == msg['seq_num']:
                    frag_rtt = float(msg['time_rcv']-d.time_rcv)*1000
                    for router in routers:
                        if router['ip'] == msg['ip']:
                            router['times'].append(frag_rtt)
    #sum rtts for each router and calculate the average
    for router in routers:
        rtt_sum = 0
        dev_rtt = 0
        est_rtt = 0
        for time in router['times']:
            sample_rtt = time
            rtt_sum = rtt_sum+time
            est_rtt = float(rtt_sum/len(router['times']))
        dev_rtt = numpy.std(router['times'])
        if router['ip'] != dst_ip:
            print('The avg RTT between %s and %s is: %dms, the s.d. is: %dms' %(src_node_ip, router['ip'], int(est_rtt), int(dev_rtt)))
    #print avg rtt and s.d for travel btwn ultimate destination node and src node
    for router in routers:
        rtt_sum = 0
        dev_rtt = 0
        est_rtt = 0
        for time in router['times']:
            sample_rtt = time
            rtt_sum = rtt_sum+time
            est_rtt = float(rtt_sum/len(router['times']))
        dev_rtt = numpy.std(router['times'])
        if router['ip'] == dst_ip:
            print('The avg RTT between %s and %s is: %dms, the s.d. is: %dms' %(src_node_ip, router['ip'], int(est_rtt), int(dev_rtt)))

    print('\n')
    return 0

def traceroute_stats(fname):
    #total packets in trace
    total_packets = 0
    #time deltas list
    time_deltas = []
    #Actual packet times computed from time deltas
    packet_times = []
    #IP protocols
    ip_protocols = []
    #win router
    win_router = {'ip': "", 'seq_num': 0, 'time_rcv': 0}
    #linux router
    linux_router = {'ip': "", 'src_port': 0, 'time_rcv': 0}
    #router ip list
    routers = []
    #all datagrams
    datagrams = []
    #error messages
    error_msgs = []
    #Ultimate source node with src and dst ips
    src_node = {'src_ip': None, 'dst_ip': None, 'protocol': None, 'src_port': None, 'dst_port': None, 'seq_num': 0}
    #open trace file
    f = open(fname, 'rb')
    pcap_obj = dpkt.pcap.Reader(f)
    #iterate through trace file
    for timestamp, buff in pcap_obj:
        total_packets = total_packets+1
        #Calculate time delta, then calculate relative time to traceroute file
        time_deltas.append(datetime.datetime.fromtimestamp(timestamp))
        packet_times.append(relative_time(time_deltas))
        #Unpack Ethernet Frame
        eth = dpkt.ethernet.Ethernet(buff)
        #Check if Ethernet frame contains IP data (datagram)
        if not isinstance(eth.data, dpkt.ip.IP):
            continue
        else:
            #Unpack ip frame
            ip = eth.data
            #Get ip header info:
            #Do-not-fragment
            DF = bool(ip.off & dpkt.ip.IP_DF)
            #More-fragments
            MF = bool(ip.off & dpkt.ip.IP_MF)
            #Fragment offset
            offset = ip.offset
            #identification number
            gram_id = ip.id
            #ttl
            ttl = ip.ttl
            #create datagram
            d = datagram(gram_id, 0, 0)
            d.time_rcv = relative_time(time_deltas)
            d.dst_ip = compute_ip_address(ip.dst)
            d.ttl = ttl
            #Add datagram to list if doesn't exist
            if find_datagram(d, datagrams) == None:
                datagrams.append(d)
            #calculate index of datagram
            index = find_datagram(d, datagrams)
            #If datagram is fragmented, update values accordingly
            if MF == True:
                if datagrams[index].num_fragments == 0:
                    datagrams[index].num_fragments = 1
                datagrams[index].num_fragments = datagrams[index].num_fragments+1
            #calculate current offset (where the next fragment should be inserted) for datagram
            datagrams[index].last_offset = offset
            #Check protocol type
            if ip.p == 1 and ip_protocols.count('1: ICMP') == 0:
                ip_protocols.append('1: ICMP')
            elif ip.p == 6 and ip_protocols.count('6: TCP') == 0:
                ip_protocols.append('6: TCP')
            elif ip.p == 17 and ip_protocols.count('17: UDP') == 0:
                ip_protocols.append('17: UDP')
            #check if datagram is ICMP or UDP
            if isinstance(ip.data, dpkt.icmp.ICMP):
                icmp = ip.data
                datagrams[index].proto = 'ICMP'
                #if ttl = 1, check if echo ping, if so... make src node
                if ip.ttl == 1 and icmp.type == 8:
                    file_type = 'WIN'
                    datagrams[index].seq_num = int(repr(icmp.data.seq))
                    if src_node.get('ip') == None and src_node.get('protocol') == None:
                        src_node['protocol'] = 'ICMP'
                        src_node['src_ip'] = compute_ip_address(ip.src)
                        src_node['dst_ip'] = compute_ip_address(ip.dst)
                #if ttl != 1 but is a ping message, record sequence number
                elif ip.ttl != 1 and icmp.type == 8:
                    datagrams[index].seq_num = int(repr(icmp.data.seq))
                #Check if ICMP error message, if it is add ip to router list
                if icmp.type == 11 or icmp.type == 3:
                    #check if WIN traceroute
                    if file_type == 'WIN':
                        seq_num = int(repr(icmp.data.data.data.data.seq))
                        addr = compute_ip_address(ip.src)
                        win_router = {'ip': addr, 'seq_num': seq_num, 'time_rcv': relative_time(time_deltas), 'ttl': 0}
                        if routers.count(win_router) == 0:
                            routers.append(win_router)
                            error_msgs.append(win_router)
                    #check if LINUX traceroute
                    elif file_type == 'LINUX':
                        udp = icmp.data
                        src_port = udp.data.data.sport
                        addr = compute_ip_address(ip.src)
                        linux_router = {'ip': addr, 'src_port': src_port, 'time_rcv': relative_time(time_deltas), 'ttl': 0}
                        if routers.count(linux_router) == 0:
                            routers.append(linux_router)
                            error_msgs.append(linux_router)
            #if UDP
            elif type(ip.data) == UDP:
                udp = ip.data
                d.src_p = udp.sport
                datagrams[index].proto = 'UDP'
                if ip.ttl == 1:
                    file_type = 'LINUX'
                    if src_node.get('ip') == None and src_node.get('protocol') == None:
                        udp = ip.data
                        src_node['protocol'] = 'UDP'
                        src_node['src_ip'] = compute_ip_address(ip.src)
                        src_node['dst_ip'] = compute_ip_address(ip.dst)
            else:
                continue
    #General Output information
    print('\nThe IP address of the source node: %s' %(src_node['src_ip']))
    print('The IP address of ultimate destination node: %s' %(src_node['dst_ip']))
    print('The IP address of the intermediate destination nodes:')
    count = 0
    router_ips = []
    #march routers to datagram and document ttl for hop count:
    if file_type == 'LINUX':
        for r in routers:
            for d in datagrams:
                if d.src_p == r['src_port']:
                    r['ttl'] = d.ttl
    elif file_type == 'WIN':
        for r in routers:
            for d in datagrams:
                if d.seq_num == r['seq_num']:
                    r['ttl'] = d.ttl
    #sort router list by ttl
    routers = sorted(routers, key=lambda k: k['ttl'])
    error_msgs = sorted(error_msgs, key=lambda k: k['ttl'])
    #print routers in order
    for router in routers:
        if router_ips.count(router['ip']) == 0:
            router_ips.append(router['ip'])
            if router['ip'] != src_node['dst_ip']:
                count = count+1
                print('router %d: %s' %(count,router['ip']))
    #iterate through protocol list
    print('\nThe values in the protocol field of IP headers:\n')
    for protocol in ip_protocols:
        print(protocol)
    count = 0
    frag_count = 0
    print("\n")
    #Calculate avg RTT and Dev RTTs for each intermdiate node
    calculate_rtts(datagrams, error_msgs, file_type, src_node['src_ip'], src_node['dst_ip'])
    for d in datagrams:
        count = count+1
        print('The number of fragments created from the original datagram D%d is: %d\n' %(count, d.num_fragments))
        print('The offset of the last fragment is: %d\n' %(d.last_offset))
    #close file
    f.close()
    return

#take tracefile name from command line
fname = sys.argv[1]+'.pcap'
traceroute_stats(fname)
