import web3

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
def parse_os(file_path):
    os_swaps = {}
    sales = load(file_path)["sales"]
    for sale in sales:  
        seller = sale["from"]
        buyer = sale["to"]
        price = int(sale["price"]["netAmount"]["raw"])
        tx_id = sale["txHash"] 
        
        if(buyer not in os_swaps):
            # eth_spent, eth_gained,emeralds_bought, emeralds_sold, tx
            os_swaps[buyer] = (0,0,0,0,[])
        os_swaps[buyer] = (
            os_swaps[buyer][0]+price, 
            os_swaps[buyer][1],
            os_swaps[buyer][2]+1,
            os_swaps[buyer][3],
            os_swaps[buyer][4] + [tx_id]
        )

        if(seller not in os_swaps):
            # eth_spent, eth_gained, emeralds_bought, emeralds_sold, tx
            os_swaps[seller] = (0,0,0,0,[])
        os_swaps[seller] = (
            os_swaps[seller][0], 
            os_swaps[seller][1]+price,
            os_swaps[seller][2],
            os_swaps[seller][3]+1,
            os_swaps[seller][4] + [tx_id]
        ) 
    return os_swaps
#parse os events
os_events = parse_os("./os_events.json")

transfer_ledger = load("./v1_event_erc721_ledger.txt")

erc20_ledger = load("./v1_event_erc20_ledger.txt")
enriched_ledger = load("./v1_event_enriched_ledger.json")
uni_swaps = load("./v1_uni_swap_balances.json")

addresses = set(enriched_ledger.keys()).union(uni_swaps.keys()).union(erc20_ledger.keys()).union(transfer_ledger.keys()).union(os_events.keys())

#format
#address, emerald_bal_transfer_ev, emerald_bal_erc20_ev, emerald_enriched_bal, eth_spent_uni, uni_tx_list, os_eth_spent, os_eth_gained, os_emeralds_bought, os_emeralds_sold, os_txs
result = [["address","emerald_bal_transfer_ev", "emerald_bal_erc20_ev", "emerald_enriched_bal", "uni_emerald_spent", "uni_eth_spent", "uni_txs_list", "os_eth_spent", "os_eth_gained", "os_emerald_boughts", "os_emeralds_sold", "os_txs"]]
for a in addresses:
    emerald_bal_transfer_ev = transfer_ledger.get(a, 0)
    emerald_bal_erc20_ev = erc20_ledger.get(a, 0)/10**6
    emerald_enriched_bal = enriched_ledger.get(a, 0)/10**6
    swap = uni_swaps.get(a,(0,0,[])) 
    uni_emerald_spent = swap[0]/10**6
    uni_eth_spent = str(swap[1]/10**18) #to eth from wei
    uni_txs_list = ", ".join(swap[2])

    os_swap = os_events.get(a, (0, 0, 0, 0, []))
    os_eth_spent = os_swap[0]/10**18 #to eth from wei
    os_eth_gained = os_swap[1]/10**18 #to eth from wei
    os_emerald_bought = os_swap[2]
    os_emeralds_sold = os_swap[3]
    os_txs = ", ".join(os_swap[4]) 


    result.append([a, emerald_bal_transfer_ev, emerald_bal_erc20_ev, emerald_enriched_bal, uni_emerald_spent, uni_eth_spent, uni_txs_list, os_eth_spent, os_eth_gained, os_emerald_bought, os_emeralds_sold, os_txs])

import csv
with open("v1_correlation.csv", 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=';')
    writer.writerows(result)

