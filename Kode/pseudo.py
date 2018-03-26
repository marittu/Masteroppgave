"""
#Connection
- Consurtium - Need ip/port from node in network to join
    - ip/port of already connected node, self ip/port
- Getpeer until 8(?) peers, receive 2 new peers from each request or connect to all peers since finite network
- Connection held for 90 minutes after last im alive
- Broadcast im alive every 30 minutes - ping/pong


#Initial sync
- Local best 
- From peer, see if local best matches -> get next 2000 headers
- From other peer, see if local best matces -> get next 2000 headers
- Continue until less than 2000 headers received, validate with one more peer
- Download blocks 
- Validate

#Store on file
- If program crashes, read in latest head_block and query peers for updates in blockchain

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

#Transactions
- Should transactions be broadcasted? Or only stored in block of node creating transactions
- How to verify that a given transaction is included in a block?

#Consensus

#Contracts
- Each party signs with private keys
- Nodes use public key to validate Contracts

- If HW signals electricity transferred from A to B
    - Transfer tokens from B to A based on amount of electricity and current price
    - 

#Tokens
- import secrets
- secrets.token_urlsafe() - base64 format
- Link a token to private key of owner - can be verified using public key?
- https://hackernoon.com/bitcoin-ethereum-blockchain-tokens-icos-why-should-anyone-care-890b868cec06:
    Want the token's value to be tied to the value of the protocol or application, similar to how a
    public company's stoke is tied to the company that issued it

#Pricing

#Unittest
- At least for blockchain and contracts 

#Procumer/Consumer
- Algorithms for deciding where to consume energy from
- Let user decide on different variables e.g. pricing and availability

#Project organizing
- One class per script? 
- Own scripts for helper functions
- Message script
- Make communication defferd and callback based

"""

#Run to completion?