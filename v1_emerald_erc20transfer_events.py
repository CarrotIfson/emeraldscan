from web3 import Web3
from dotenv import dotenv_values
import codecs
from multiprocessing import Process, Queue 
from time import sleep
import json

def decode(hex):
    return codecs.decode(hex, 'hex').decode('utf-8')

def parse_blocks(contract_address, contract_abi, initial_block, last_block, worker_id, queue):  
    erc20transfer_events = set()
    contract = w3.eth.contract(address=w3.to_checksum_address(contract_address), abi=contract_abi)  
    for x in range(initial_block, last_block+1): 
        events = contract.events.ERC20Transfer.get_logs(fromBlock=x, toBlock=x)
        if (events!=()):
            for event in events:   
                tx_hash = event["transactionHash"].hex()  
                block = event["blockNumber"]
                sender = event["args"]["from"]
                receiver = event["args"]["to"]
                amount = event["args"]["amount"] 
                erc20transfer_events.add((tx_hash,block,sender,receiver,amount))
        if(x % 300 == 0):
            print(f"Worker {worker_id} still working...")
    
    print(f"Worker {worker_id} found {len(erc20transfer_events)} TRANSFER events")  

    queue.put({"erc20transfer_events":erc20transfer_events, "worker_id":worker_id})
    

config = dotenv_values(".env")

EMERALD_V1_ADR = config.get("EMERALD_V1_ADR")
EMERALD_V1_FBLOCK=int(config.get("EMERALD_V1_FBLOCK"))
EMERALD_V1_LBLOCK=int(config.get("EMERALD_V1_LBLOCK"))
EMERALD_V1_ABI=config.get("EMERALD_V1_ABI")

ALCHEMY_HTTP_ENDPOINT = config.get("ALCHEMY_HTTP_ENDPOINT").split(",")[2]

w3 = Web3(Web3.HTTPProvider(ALCHEMY_HTTP_ENDPOINT))
if __name__ == '__main__':
    print(w3.is_connected())
    erc20transfer_events = set()
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
            parse_blocks(EMERALD_V1_ADR, EMERALD_V1_ABI, first_block, last_block, p, queue)
        else:
            print(f"Worker #{p} will process from {first_block} to {last_block}")
            process = Process(target=parse_blocks, args=(EMERALD_V1_ADR, EMERALD_V1_ABI, first_block, last_block, p, queue))   
            workers_list.append(process)    
            process.start()

    #CLOSE THREADS
    for p in range(0,num_process):
        result = queue.get()   
        finished_worker = result["worker_id"]
        workers_list[finished_worker].join()
        erc20transfer_events.update(result["erc20transfer_events"])
        
    print("All workers finished")

    #store all TRANSFER events 
    with open("./v1_erc20transfer_events.json", "w") as file:
        json.dump(list(erc20transfer_events), file)

    #build ledger
    erc20transfer_ledger = {}
    #key: address
    #value: (in_tx_count, out_tx_count, amount_in, amount_out, balance)
    for event in erc20transfer_events:
        # event = (tx_hash,block,sender,receiver,amount)
        tx_hash = event[0]
        sender = event[2]
        receiver = event[3]
        amount = event[4]
        if(sender not in erc20transfer_ledger):
            erc20transfer_ledger[sender] = (0,0,0,0,0,[])  
        sender_in_tx = erc20transfer_ledger[sender][0]
        sender_out_tx = erc20transfer_ledger[sender][1]+1
        sender_amount_in = erc20transfer_ledger[sender][2]
        sender_amount_out = erc20transfer_ledger[sender][3]+amount
        sender_balance = erc20transfer_ledger[sender][4]-amount
        senders_txs = erc20transfer_ledger[sender][5] + [tx_hash]
        erc20transfer_ledger[sender] = (sender_in_tx, sender_out_tx, sender_amount_in, sender_amount_out, sender_balance, senders_txs)

        if(receiver not in erc20transfer_ledger,[]):
            erc20transfer_ledger[receiver] = (0,0,0,0,0,[])
        receiver_in_tx = erc20transfer_ledger[receiver][0]+1
        receiver_out_tx = erc20transfer_ledger[receiver][1]
        receiver_amount_in = erc20transfer_ledger[receiver][2]+amount
        receiver_amount_out = erc20transfer_ledger[receiver][3]
        receiver_balance = erc20transfer_ledger[receiver][4]+amount
        receiver_txs = erc20transfer_ledger[sender][5] + [tx_hash]
        erc20transfer_ledger[receiver] = (receiver_in_tx, receiver_out_tx, receiver_amount_in, receiver_amount_out, receiver_balance, receiver_txs)

    #store TRANSFER ledger events 
    with open("./v1_erc20transfer_ledger.json", "w") as file:
        json.dump(erc20transfer_ledger, file)