from web3 import Web3
from dotenv import dotenv_values
import codecs
from multiprocessing import Process, Queue 
from time import sleep
import json

def decode(hex):
    return codecs.decode(hex, 'hex').decode('utf-8')

def parse_blocks(contract_address, contract_abi, initial_block, last_block, worker_id, queue):  
    swap_events = set()
    contract = w3.eth.contract(address=w3.to_checksum_address(contract_address), abi=contract_abi)  
    for x in range(initial_block, last_block+1): 
        events = contract.events.Swap.get_logs(fromBlock=x, toBlock=x)
        if (events!=()):
            for event in events:  
                tx_hash = event["transactionHash"].hex()  
                block = event["blockNumber"]
                sender = w3.eth.get_transaction(tx_hash)["from"]
                receiver = event["args"]["recipient"] 
                emerald_amount = event["args"]["amount0"]
                eth_amount = event["args"]["amount1"] 
                swap_events.add((tx_hash,block,sender,receiver,emerald_amount,eth_amount)) 
        if(x % 300 == 0):
            print(f"Worker {worker_id} still working...")
    
    print(f"Worker {worker_id} found {len(swap_events)} SWAP events")  
    queue.put({"swap_events":swap_events, "worker_id":worker_id})
    

config = dotenv_values(".env")

EMERALD_V1_FBLOCK=int(config.get("EMERALD_V1_FBLOCK"))
EMERALD_V1_LBLOCK=int(config.get("EMERALD_V1_LBLOCK"))
UNI_V1_POOL_ADR = config.get("V1_UNI_POOL_ADDR")
UNI_V1_POOL_ABI = config.get("V1_UNI_POOL_ABI")

ALCHEMY_HTTP_ENDPOINT = config.get("ALCHEMY_HTTP_ENDPOINT").split(",")[1]

w3 = Web3(Web3.HTTPProvider(ALCHEMY_HTTP_ENDPOINT))
if __name__ == '__main__':
    print(w3.is_connected())
    swap_events = set()
    #multiprocess logic
    num_process = 4
    block_step = int((EMERALD_V1_LBLOCK - EMERALD_V1_FBLOCK) / num_process)
    workers_list = []
    queue = Queue()

    print(f"Each worker will process {block_step} blocks")
    #START THREADS
    for p in range(0,num_process):
        first_block = EMERALD_V1_FBLOCK + (block_step * p)
        last_block = first_block + block_step  - 1
        if(num_process == 1):
            parse_blocks(UNI_V1_POOL_ADR, UNI_V1_POOL_ABI, first_block, last_block, p, queue)
        else:
            print(f"Worker #{p} will process from {first_block} to {last_block}")
            process = Process(target=parse_blocks, args=(UNI_V1_POOL_ADR, UNI_V1_POOL_ABI, first_block, last_block, p, queue))   
            workers_list.append(process)    
            process.start()

    #CLOSE THREADS
    for p in range(0,num_process):
        result = queue.get()   
        finished_worker = result["worker_id"]
        workers_list[finished_worker].join()
        swap_events.update(result["swap_events"])
        
    print("All workers finished")

    #store all TRANSFER events 
    with open("./v1_swap_events.json", "w") as file:
        json.dump(list(swap_events), file)

    #build ledger
    swap_ledger = {}
    #key: address
    #value: (emerald_in, emerald_out, eth_in, eth_out, emerald_received, eth_received, tx_list)
    for event in swap_events:
        # event = (tx_hash,block,sender,receiver,emerald_amount,eth_amount)
        tx_hash = event[0]
        sender = event[2]
        receiver = event[3]
        emerald_amount = event[4]
        eth_amount = event[5]

        if(sender not in swap_ledger):
            swap_ledger[sender] = (0, 0, 0, 0, 0, 0, [])
            
        if(emerald_amount<0):
            sender_emerald_in = swap_ledger[sender][0]-emerald_amount
            sender_emerald_out = swap_ledger[sender][1]
            sender_eth_in = swap_ledger[sender][2]
            sender_eth_out = swap_ledger[sender][3]+eth_amount
        else:
            sender_emerald_in = swap_ledger[sender][0]
            sender_emerald_out = swap_ledger[sender][1]+emerald_amount 
            sender_eth_in = swap_ledger[sender][2]-eth_amount
            sender_eth_out = swap_ledger[sender][3]
        sender_emerald_received = swap_ledger[sender][4]
        sender_eth_received = swap_ledger[sender][5]

        sender_txs = swap_ledger[sender][6] + [tx_hash]
        swap_ledger[sender] = (sender_emerald_in,sender_emerald_out,sender_eth_in,sender_eth_out,sender_emerald_received,sender_eth_received,sender_txs)

        if(sender != receiver): 
            if(receiver not in swap_ledger):
                swap_ledger[receiver] = (0, 0, 0, 0, 0, 0, [])
            receiver_emerald_in = swap_ledger[receiver][0]
            receiver_emerald_out = swap_ledger[receiver][1]
            receiver_eth_in = swap_ledger[receiver][2]
            receiver_eth_out = swap_ledger[receiver][3]
            if(emerald_amount < 0): 
                receiver_emerald_received = swap_ledger[receiver][4]-emerald_amount
                receiver_eth_received = swap_ledger[receiver][5]
            else:
                receiver_emerald_received = swap_ledger[receiver][4]
                receiver_eth_received = swap_ledger[receiver][5]-eth_amount

            receiver_txs = swap_ledger[receiver][6] + [tx_hash]
            swap_ledger[receiver] = (receiver_emerald_in,receiver_emerald_out,receiver_eth_in,receiver_eth_out,receiver_emerald_received,receiver_eth_received,receiver_txs)


    #store TRANSFER ledger events 
    with open("./v1_swap_ledger.json", "w") as file:
        json.dump(swap_ledger, file) 