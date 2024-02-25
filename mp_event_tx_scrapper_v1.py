from web3 import Web3
from dotenv import dotenv_values
import codecs
from multiprocessing import Process, Queue 
from time import sleep
import json

def decode(hex):
    return codecs.decode(hex, 'hex').decode('utf-8')

def parse_blocks(contract_address, contract_abi, initial_block, last_block, worker_id, queue):  
    txs_with_erc20 = set()
    txs_with_erc721 = set()
    contract = w3.eth.contract(address=w3.to_checksum_address(contract_address), abi=contract_abi)  
    for x in range(initial_block, last_block+1):
        #print(f"Worker {worker_id} on block {x}")
        events = contract.events.Transfer.get_logs(fromBlock=x, toBlock=x+1)
        if (events!=()):
            for event in events: 
                tx_hash = event["transactionHash"].hex()  
                txs_with_erc721.add(tx_hash)
        events = contract.events.ERC20Transfer.get_logs(fromBlock=x, toBlock=x)
        if (events!=()):
            for event in events:  
                tx_hash = event["transactionHash"].hex()  
                txs_with_erc20.add(tx_hash)
        if(x % 300 == 0):
            print(f"Worker {worker_id} still working...")
    
    print(f"Worker {worker_id} found {len(txs_with_erc721)} erc721 events") 
    print(f"Worker {worker_id} found {len(txs_with_erc20)} erc20 events") 
    queue.put({"txs_with_erc721":txs_with_erc721, "txs_with_erc20":txs_with_erc20, "worker_id":worker_id})
    

config = dotenv_values(".env")

EMERALD_V1_ADR = config.get("EMERALD_V1_ADR")
EMERALD_V1_FBLOCK=int(config.get("EMERALD_V1_FBLOCK"))
EMERALD_V1_LBLOCK=int(config.get("EMERALD_V1_LBLOCK"))
EMERALD_V1_ABI=config.get("EMERALD_V1_ABI")

EMERALD_V2_ADR = config.get("EMERALD_V2_ADR")
EMERALD_V2_FBLOCK=config.get("EMERALD_V2_FBLOCK")
EMERALD_V2_LBLOCK=config.get("EMERALD_V2_LBLOCK")

ETHERSCAN_API_KEY = config.get("ETHERSCAN_API_KEY")
ALCHEMY_API_KEY = config.get("ALCHEMY_API_KEY")
ALCHEMY_HTTP_ENDPOINT = config.get("ALCHEMY_HTTP_ENDPOINT")

w3 = Web3(Web3.HTTPProvider(ALCHEMY_HTTP_ENDPOINT))
if __name__ == '__main__':
    print(w3.is_connected())
    txs_with_erc20 = set()
    txs_with_erc721 = set()
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
        process = Process(target=parse_blocks, args=(EMERALD_V1_ADR, EMERALD_V1_ABI, first_block, last_block, p, queue))  
        workers_list.append(process)
        process.start()

    #CLOSE THREADS
    for p in range(0,num_process):
        result = queue.get()   
        finished_worker = result["worker_id"]
        #print(f"Worker {finished_worker} has {len(result["txs_with_erc721"])} txs with erc721 events") 
        #print(f"Worker {finished_worker} has {len(result["txs_with_erc20"])} txs with erc20 events") 
        workers_list[finished_worker].join()
        txs_with_erc20.update(result["txs_with_erc20"])
        txs_with_erc721.update(result["txs_with_erc721"])
        #rint(f"joined worker {finished_worker}")
    print("All workers finished")
    
    print(f"EmeraldV1 has {len(txs_with_erc20)} txs with erc20 events") 
    print(f"EmeraldV1 has {len(txs_with_erc721)} txs with erc721 events") 
    
    
    with open("./v1_erc20_txs.txt", "w") as file:
        json.dump(list(txs_with_erc20), file)
    with open("./v1_erc721_txs.txt", "w") as file:
        json.dump(list(txs_with_erc721), file)
 

    