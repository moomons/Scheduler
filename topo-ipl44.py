"""

mons topology

version 0.10

Commandline:
sudo mn --custom ~/Scheduler/ipl44.py --topo=monstopo

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=monstopo' from the command line.

"""

from mininet.topo import Topo

class monsTopo( Topo ):
    "IPL Lab 4 switch 4 host topology"

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )

        # Add hosts and switches
        ipl201 = self.addHost( 'h1-201' )
        ipl211 = self.addHost( 'h2-211' )
        ipl212 = self.addHost( 'h3-212' )
        ipl213 = self.addHost( 'h4-213' )

        ipl214 = self.addSwitch( 's1-214' )
        ipl215 = self.addSwitch( 's2-215' )
        ipl224 = self.addSwitch( 's3-224' )
        ipl225 = self.addSwitch( 's4-225' )

        # Add links
        self.addLink( ipl214, ipl225, 4, 1 )
        self.addLink( ipl214, ipl224, 3, 1 )
        self.addLink( ipl215, ipl225, 4, 2 )
        self.addLink( ipl215, ipl224, 3, 2 )

        self.addLink( ipl215, ipl201, 2, 2 )
        self.addLink( ipl215, ipl211, 1, 2 )
        self.addLink( ipl214, ipl212, 1, 2 )
        self.addLink( ipl214, ipl213, 2, 2 )

topos = { 'monstopo': ( lambda: monsTopo() ) }
