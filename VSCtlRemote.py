'''
remote control for ovs-vsctl command

written by Ping Lu
'''

import os
import re


class VSCtlRemote:
  def __init__(self):
    print 'remote control for ovs-vsctl command \n'


  def ShowBridge(self, OVSServerIP):
    cmd = 'sudo ovs-vsctl --db=tcp:' + OVSServerIP + ':6640 show'
    os.system(cmd)
    return  


  def AddQueue(self, OVSServerIP, OVSPort, min_rate, max_rate):
    cmd = 'sudo ovs-vsctl --db=tcp:' + OVSServerIP + ':6640 -- set port ' + OVSPort + \
          ' qos=@newqos -- --id=@newqos create qos type=linux-htb queues=0=@q0' + \
          ' -- --id=@q0 create queue other-config:min-rate=' + str(min_rate) + ' other-config:max-rate=' + str(max_rate)
    output = os.popen(cmd)
    uuid = output.read()
    #error processing, have not found a good method for error processing
    
    stats = 1 
    ids = uuid.split('\n')
    qos_id = ids[0]
    queue_id = ids[1]
    return (stats, qos_id, queue_id)
    
    queue_name = 'aha'
    return queue_name


  def AddTwoQueues(self, OVSServerIP, OVSPort, q0_min_rate, q0_max_rate, q1_min_rate, q1_max_rate):
    cmd = 'sudo ovs-vsctl --db=tcp:' + OVSServerIP + ':6640 -- set port ' + OVSPort + \
          ' qos=@newqos -- --id=@newqos create qos type=linux-htb queues=0=@q1,1=@q2' + \
          ' -- --id=@q1 create queue other-config:min-rate=' + str(q0_min_rate) + ' other-config:max-rate=' + str(q0_max_rate) + \
          ' -- --id=@q2 create queue other-config:min-rate=' + str(q1_min_rate) + ' other-config:max-rate=' + str(q1_max_rate)
    output = os.popen(cmd)
    uuid = output.read()
    #error processing, have not found a good method for error processing
    
    stats = 1    
    ids = uuid.split('\n')
    qos_id = ids[0]
    queues_id = ids[1:]

    return (stats, qos_id, queues_id)

  def DelQos(self, OVSServerIP, qos_uuid):
    # we get queues belong to this qos first, then we delete the qos and all the corresonding queues
    cmd = 'sudo ovs-vsctl --db=tcp:' + OVSServerIP + ':6640 get qos ' + qos_uuid + ' queues'
    output = os.popen(cmd)
    queues = output.read()
    queues = re.split('=|,|}', queues)
    queues = queues[1::2]
    cmd = 'sudo ovs-vsctl --db=tcp:' + OVSServerIP + ':6640 destroy qos ' + qos_uuid
    output = os.popen(cmd)
    output = output.read()
    stats = 1
    if len(output) > 0:        
        print 'something error when qos destorying \n'
        stats = 0
    for q_id in queues:
        cmd = 'sudo ovs-vsctl --db=tcp:' + OVSServerIP + ':6640 destroy queue ' + q_id
        output = os.popen(cmd)
        output = output.read()
        if len(output) > 0:
            print 'something error when queue destroying \n'
            stats = 0

    return stats         


  def DelQueue(self, OVSServerIP, queue_uuid):
    # we get the qos of this queue first, and then invoke DelQos to delete the qos and the queue
    # thic function has not implemented yet

    return 1 


  def ListQos(self, OVSServerIP):
    cmd = 'sudo ovs-vsctl --db=tcp:' + OVSServerIP + ':6640 list qos'
    output = os.popen(cmd)
    qos = output.read()
    qos = qos.split('\n\n')
    qos_array = []
    qos_num = len(qos)
    for q in qos:
        iterms = re.split(': |\n', q)
        q_dict = {'uuid': iterms[1], 'external_ids': iterms[3], 'other_config': iterms[5], 'queues': iterms[7], 'type': iterms[9]}
        qos_array.append(q_dict)

    return (qos_num, qos_array)

  def ListQueue(self, OVSServerIP):
    cmd = 'sudo ovs-vsctl --db=tcp:' + OVSServerIP + ':6640 list queue'
    output = os.popen(cmd)
    queues = output.read()
    queues = queues.split('\n\n')
    que_array = []
    que_num = len(queues)
    for queue in queues:
        iterms = re.split(': |\n', queue)
        que_dict = {'uuid': iterms[1], 'dscp': iterms[3], 'external_ids': iterms[5], 'other_config': iterms[7]}
        que_array.append(que_dict)
    
    return (que_num, que_array)

















