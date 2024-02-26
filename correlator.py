#load ledger
def load(file_path):
    try:
        with open(file_path, 'r') as file: 
            content = file.read() 
            loaded_list = eval(content)
            return loaded_list 
    except Exception as e:
        print(f"Exception{e}")
        return None


enriched_ledger = load("./v1_event_enriched_ledger.json")
uni_swaps = load("./v1_uni_swap_balances.json")

addresses = set(enriched_ledger.keys()).union(uni_swaps.keys())

#format
#address, emerald_balance, emerald_swapped, eth_swapped, txs_list
result = {}
for a in addresses:
    emerald_balance = enriched_ledger.get(a, 0)
    swaps = uni_swaps.get(a,(0,0,[])) 
    emerald_swapped = swaps[0]
    eth_swapped = swaps[1]
    txs_list = swaps[2]
    result[a] = (emerald_balance, emerald_swapped, eth_swapped, txs_list)


import json
with open("./correlation.json", "w") as file:
    json.dump(result, file)

