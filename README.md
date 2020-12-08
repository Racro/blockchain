# blockchain
Assignment - CS765 
170050030 170050056

#PART 1

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


#PART 2

## Block Header
We have used a list to represent the block header. It contains Previous Block Hash, Merkel root and Timestamp. Body of the block is empty and hash of this list is taken to calculate the hash of the block

## Block Mining
Inter-arrival time is taken as a constant = 10 seconds
Waiting Time is used as hack for emulating the PoW

## Database (or Blockchain)
Each Node has a local copy of the blockchain. The database is stored as a dictionary with key as the height of block and values as a list of blocks (at that particular height)

## Broadcasting the block
A global hash table is used for each node to check whether the particular block has passed through it before or not. If not, the block is validated and transmitted to all its peers

## Pending Queue
Pending Queue is a list which contains all the blocks which are yet to be validated and incorporated at each node. A node processes it on O(n2) time as every block is dependednt of other block in the list for its incorporation in the blockchain. 

## Adversary
An adversary is someone who has a particular amount of hashing power and floods a particular percentage of nodes. We have, in our implementation, made only 1 node as adversary and it performs the required malicious behaviour. The remaining honest mining hash power is distributed amnogst all other nodes equally.

## Flow of Events
* A node joins the network and asks its peers to send it their latest block on which they are mining (Bk)
* After receiving Bk from all the peers, it checks which block has the latest timestamp
* It chooses the node corresponsing to that block and asks for B0 to Bk-1 from it
* The peer node sends it the longest chain in its database on whihc it is mining
* After receving the blocks, it updates its database and starts mining

## Mining power utilization
Mining power utilization is the ratio of the number of blocks in the longest chain to the total number of blocks in the blockchain (including forks)

## File Structure


## How to Run
