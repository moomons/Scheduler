from pycon_cfg import *


def showsingleflowstat(flow):
    average_delay = 1000 * float(flow['average_delay'])  # ms
    average_jitter = 1000 * float(flow['average_jitter'])  # ms
    average_bitrate = float(flow['average_bitrate']) / 1000.0  # Mbps
    average_pkts_droprate = float(flow['pkts_dropped_rate'])  # pct

    logger.info("From " + flow['ipport_source'] + " to " + flow['ipport_destination'] +
                ": Delay=%.3f ms" % average_delay +
                ",\tJitter=%.3f ms" % average_jitter +
                ",\tBitrate=%.3f Mbps" % average_bitrate +
                ",\tDroprate=%.2f %%" % average_pkts_droprate)


def showstat(list, title):
    listlen = len(list)

    sumavgdelay = sumavgjitter = sumavgbitrate = sumpktsdroprate = 0.0
    for flow in list:
        sumavgdelay += float(flow['average_delay'])
        sumavgjitter += float(flow['average_jitter'])
        sumavgbitrate += float(flow['average_bitrate'])
        sumpktsdroprate += float(flow['pkts_dropped_rate'])
        showsingleflowstat(flow)

    average_delay = 1000 * sumavgdelay / listlen  # ms
    average_jitter = 1000 * sumavgjitter / listlen  # ms
    average_bitrate = sumavgbitrate / 1000.0 / listlen  # Mbps
    average_pkts_droprate = sumpktsdroprate / listlen  # pct

    logger.info(title + "Delay=%.3f ms" % average_delay +
          ",\tJitter=%.3f ms" % average_jitter +
          ",\tBitrate=%.3f Mbps" % average_bitrate +
          ",\tDroprate=%.2f %%" % average_pkts_droprate)


def parsetestout(out):
    result_lowlatency = []
    result_highbandwidth = []
    flows = out.split("----------------------------------------------------------"
                      "\n----------------------------------------------------------\n")
    for flow in flows:
        lines = flow.split('\n')
        flag_flowstart = False
        flowinfo = {}
        for line in lines:
            # print(line)
            if line.startswith("Flow number:"):
                flag_flowstart = True
                flowinfo['flow_number'] = line.split(": ")[1]
            elif flag_flowstart:
                if line.startswith("From "):
                    flowinfo['ipport_source'] = line.split("10.0.0.")[1]
                elif line.startswith("To "):
                    flowinfo['ipport_destination'] = line.split("10.0.0.")[1]
                elif line.startswith("Average delay"):
                    flowinfo['average_delay'] = line.split("=")[1].lstrip().rstrip(' s')
                elif line.startswith("Average jitter"):
                    flowinfo['average_jitter'] = line.split("=")[1].lstrip().rstrip(' s')
                elif line.startswith("'Delay standard deviation"):
                    flowinfo['delay_stdev'] = line.split("=")[1].lstrip()
                elif line.startswith("Average bitrate"):
                    flowinfo['average_bitrate'] = line.split("=")[1].lstrip().rstrip(' Kbit/s')
                elif line.startswith("Packets dropped"):
                    flowinfo['pkts_dropped_rate'] = line.split("=")[1].lstrip().split("(")[1].rstrip(' %)')
                elif line.startswith("****************  TOTAL RESULTS"):
                    break
        portdst = flowinfo['ipport_destination'].split(':')[1]
        if portdst.startswith("2"):
            result_lowlatency.append(flowinfo)
        elif portdst.startswith("3"):
            result_highbandwidth.append(flowinfo)

    showstat(result_lowlatency, "Low latency:\t")
    showstat(result_highbandwidth, "High bandwidth:\t")


def main():
    file = open('out.txt', 'r')
    out = file.read()
    file.close()
    # print(out)
    parsetestout(out)


if __name__ == '__main__':
    main()

