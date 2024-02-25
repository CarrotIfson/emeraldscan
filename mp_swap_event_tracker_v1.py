from web3 import Web3
from dotenv import dotenv_values
import codecs
from multiprocessing import Process, Queue 
from time import sleep
import json

def decode(hex):
    return codecs.decode(hex, 'hex').decode('utf-8')

def parse_blocks(uniswap_address, uniswap_abi, emerald_address, initial_block, last_block, worker_id, queue):  
    swaps = []
    contract = w3.eth.contract(address=w3.to_checksum_address(uniswap_address), abi=uniswap_abi)  
    for x in range(initial_block, last_block+1):   
        events = contract.events.Swap.get_logs(fromBlock=x, toBlock=x)
        if (events!=()):
            for event in events:  
                args = event["args"]
                amount_emerald = args["amount0"]
                amount_eth = args["amount1"]
                tx_hash = event["transactionHash"].hex()
                sender = w3.eth.get_transaction(tx_hash)["from"]
                recipient = args["recipient"] 
                swaps.append((sender, recipient, amount_emerald, amount_eth, tx_hash))
                
        if(x % 300 == 0):
            print(f"Worker {worker_id} still working...")
    
    print(f"Worker {worker_id} found {len(swaps)} swap events")  
    queue.put({"swaps":swaps, "worker_id":worker_id})
    

config = dotenv_values(".env")

EMERALD_V1_ADR = config.get("EMERALD_V1_ADR")
EMERALD_V1_FBLOCK=int(config.get("EMERALD_V1_FBLOCK"))
EMERALD_V1_LBLOCK=int(config.get("EMERALD_V1_LBLOCK"))
EMERALD_V1_ABI=config.get("EMERALD_V1_ABI")

ETHERSCAN_API_KEY = config.get("ETHERSCAN_API_KEY")
ALCHEMY_API_KEY = config.get("ALCHEMY_API_KEY")
ALCHEMY_HTTP_ENDPOINT = config.get("ALCHEMY_HTTP_ENDPOINT")

V1_UNI_POOL_ADDR = config.get("V1_UNI_POOL_ADDR")
V1_UNI_POOL_ABI = config.get("V1_UNI_POOL_ABI")

w3 = Web3(Web3.HTTPProvider(ALCHEMY_HTTP_ENDPOINT))
if __name__ == '__main__':
    print(w3.is_connected())
    swaps = set()
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
        print(f"Worker #{p} will process from {first_block} to {last_block}")
        #parse_blocks(V1_UNI_POOL_ADDR, V1_UNI_POOL_ABI, EMERALD_V1_ADR, first_block, last_block, p, queue)
        process = Process(target=parse_blocks, args=(V1_UNI_POOL_ADDR, V1_UNI_POOL_ABI, EMERALD_V1_ADR, first_block, last_block, p, queue))  
        workers_list.append(process)
        process.start()

    #CLOSE THREADS
    for p in range(0,num_process):
        result = queue.get()   
        finished_worker = result["worker_id"]
        #print(f"Worker {finished_worker} has {len(result["txs_with_erc721"])} txs with erc721 events") 
        #print(f"Worker {finished_worker} has {len(result["txs_with_erc20"])} txs with erc20 events") 
        workers_list[finished_worker].join()
        swaps.update(result["swaps"])
        #rint(f"joined worker {finished_worker}")
    print("All workers finished")
    
    print(f"EmeraldV1 has {len(swaps)} swap events") 
    
    
    with open("./swaps.txt", "w") as file:
        json.dump(list(swaps), file)

    