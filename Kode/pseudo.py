"""
#Connection
- Consurtium - Need ip/port from node in network to join
    - args initial or ip/port of already connected node, self ip/port
    - If initializing connection - client
    - If connection requested - server
- Getpeer until 8(?) peers, receive 2 new peers from each request
- Connection held for 90 minutes after last im alive
- Broadcast im alive every 30 minutes - ping/pong

#Initial sync
- Local best 
- From peer, see if local best matches -> get next 2000 headers
- From other peer, see if local best matces -> get next 2000 headers
- Continue until less than 2000 headers received, validate with one more peer
- Download blocks 
- Validate

#Validation
- For header: index, previous hash, timestamp (increasing time or time in acceptable range for new blocks)
- For block: Merkel tree

#Messages
- peer handles sending and receving of Messages
- module for parsing and handling messages based on message type. Calling other modules based on message type
- module for sending messges, including message type, recipient and message. Called from other modules

#Block broadcasting 
- Creater of block sends full block to all connected peers
- Rely peers sends header to peers, if getdata received -> sends full block

#Consensus

#Contracts

#Prizing

#ID/keys

"""

#Run to completion?