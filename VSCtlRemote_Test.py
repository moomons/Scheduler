import VSCtlRemote

def test():
    ip = '192.168.109.225'
    vsctl = VSCtlRemote.VSCtlRemote()
    print '******* show bridge *********'
    vsctl.ShowBridge(ip)

    print '\n *** add two queues & bandwidth limitation ****'
    (stats, qos_id, queues_id) = vsctl.AddTwoQueues(ip, 'eth1', 10000000, 100000000, 1000000, 10000000)
    print stats, qos_id, queues_id

    print '\n ******** add one queue **************'
    (stats, qos_id, queue_id) = vsctl.AddQueue(ip, 'eth1', 20000000, 200000000)
    print stats, qos_id, queue_id
    
    print '\n ******* list qos ***********'
    (qos_num, qos_array) = vsctl.ListQos(ip) 
    print qos_num, qos_array
    print '\n ******* list queues ***********'
    (que_num, que_array) = vsctl.ListQueue(ip)   
    print que_num, que_array
    

    print '\n ******* delete queues **********'
    qos_id = qos_array[0]['uuid']    
    stats = vsctl.DelQos(ip, qos_id)
    print stats, 'qos_id = ', qos_id


if __name__ == '__main__':
    test()


