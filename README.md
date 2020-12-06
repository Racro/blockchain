# blockchain
Assignment - CS765 

## Config file
`IP` and `Port` of seed nodes __Hard-Coded__

## Peer Node
* Connects to `least_integer(n/2)+1` seed nodes 
* Randomly connects to a max. of 4 peer nodes from the union of peer list of seed nodes
* Generates `10` gossip messages from the time its active with time-difference of `5` seconds
* Generates __liveliness message__ every `13` seconds
* Contains a __ML__ (message list)  with `hash` of msg and info about which of its connected peers it has sent the message to or received the message from

## Seed Node 
* Maintains list (__PL__) of `IP address` and `port number` pairs of peers that have connected to it
* Registration request by peer node triggers an event at the seed node to add an entry containing the peer’s IP and port number to the PL

## Gossip msg
* Peer generates msg of the format: 
`self.timestamp`:`self.IP`:`self.Msg#`

## liveliness msg
If 3 consecutive liveness messages are not replied to, the node will notify the seed nodes that it is connected to, that this particular IP Address is not responding

### Request Message Format
`Liveness Request`:`self.timestamp`:`self.IP`

### Reply Message Format
`Liveness Reply`:`sender.timestamp`:`sender.IP`:`self.IP`

## Reporting the node as ’Dead’
When 3 consecutive liveness requests do not receive a reply, the peer sends a message of the following format to all the seeds it is connected to:
`Dead Node`:`DeadNode.IP`:`self.timestamp`:`self.IP`

## How to Run
__Terminal1 (seed)__ `python3 seed.py 0 1` (creates 2 seed threads using lines 0-1 of config.csv)
__Terminal2 (peer)__ `python3 peer.py` (creates 2 peer threads by default on localhost)  

