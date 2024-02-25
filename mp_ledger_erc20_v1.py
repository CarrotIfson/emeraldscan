from web3 import Web3
from dotenv import dotenv_values
import codecs
from multiprocessing import Process, Queue 
from time import sleep
import json

def decode(hex):
    return codecs.decode(hex, 'hex').decode('utf-8')

def parse_blocks(contract_address, contract_abi, initial_block, last_block, worker_id, queue):  
    erc20_ledger = []
    contract = w3.eth.contract(address=w3.to_checksum_address(contract_address), abi=contract_abi)  
    for x in range(initial_block, last_block+1):
        events = contract.events.ERC20Transfer.get_logs(fromBlock=x, toBlock=x)
        if (events!=()):
            print(events)
            for event in events:  
                args = event["args"] 
                tx_hash = event["transactionHash"].hex()  
                erc20_ledger.append((args["from"], args["to"], int(args["amount"]), tx_hash))
        if(x % 300 == 0):
            print(f"Worker {worker_id} still working...")
    
    print(f"Worker {worker_id} found {len(erc20_ledger)} erc20 events") 
    queue.put({"erc20_ledger":erc20_ledger, "worker_id":worker_id})
    

config = dotenv_values(".env")

EMERALD_V1_ADR = config.get("EMERALD_V1_ADR")
EMERALD_V1_FBLOCK=int(config.get("EMERALD_V1_FBLOCK"))
EMERALD_V1_LBLOCK=int(config.get("EMERALD_V1_LBLOCK"))
EMERALD_V1_ABI=config.get("EMERALD_V1_ABI")

ETHERSCAN_API_KEY = config.get("ETHERSCAN_API_KEY")
ALCHEMY_API_KEY = config.get("ALCHEMY_API_KEY")
ALCHEMY_HTTP_ENDPOINT = config.get("ALCHEMY_HTTP_ENDPOINT")

w3 = Web3(Web3.HTTPProvider(ALCHEMY_HTTP_ENDPOINT))
if __name__ == '__main__':
    print(w3.is_connected())
    txs_with_erc20 = set()
    txs_with_erc721 = set()
    #multiprocess logic
    num_process = 1
    block_step = int((EMERALD_V1_LBLOCK - EMERALD_V1_FBLOCK) / num_process)
    workers_list = []
    queue = Queue()

    print(f"Each worker will process {block_step} blocks")
    #START THREADS
    for p in range(0,num_process):
        first_block = EMERALD_V1_FBLOCK + (block_step * p)
        last_block = first_block + block_step  - 1 
        print(f"Worker #{p} will process from {first_block} to {last_block}")
        process = Process(target=parse_blocks, args=(EMERALD_V1_ADR, EMERALD_V1_ABI, first_block, last_block, p, queue))  
        workers_list.append(process)
        process.start()

    #CLOSE THREADS
    erc20_ledger = {}
    for p in range(0,num_process):
        result = queue.get()   
        for r in result["erc20_ledger"]:
            sender = r[0]
            receiver = r[1]
            amount = r[2]  
            if(erc20_ledger.get(sender, None) is None):
                erc20_ledger[sender] = -amount
            else:
                erc20_ledger[sender] = erc20_ledger[sender]-amount

            if(erc20_ledger.get(receiver, None) is None):
                erc20_ledger[receiver] = amount
            else:
                erc20_ledger[receiver] = erc20_ledger[receiver]+amount

        finished_worker = result["worker_id"]
        workers_list[finished_worker].join()
        print(f"joined worker {finished_worker}")
    print("All workers finished")

    with open("./v1_event_erc20_ledger.txt", "w") as file:
        json.dump(erc20_ledger, file)
 

    