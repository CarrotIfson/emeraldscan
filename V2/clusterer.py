import web3
from math import floor

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
def csv_reader(file_path):
    import csv
    data_list = []
    with open(file_path, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=";")
        for row in csvreader:
            data_list.append(row)
    return data_list
    
def parse_os(file_path):
    os_swaps = {}
    sales = load(file_path)["sales"]
    for sale in sales:  
        seller = web3.Web3.to_checksum_address(sale["from"])
        buyer = web3.Web3.to_checksum_address(sale["to"])
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

        if(buyer == '0x0B8a49d816Cc709B6Eadb09498030AE3416b66Dc'):
            print("asdsad")
    return os_swaps
def dec(val):
    return float(val)-floor(val)

def fmt(val):
    return float(format(val, ".4"))

def dictify(values): 
    res = dict()
    for h in range(len(headers)):
       res[headers[h]] = values[h]
    return res


def parse_transfers(tx_list):
    res = {}
    for tx in tx_list:
        if(tx not in res):
            res[tx] = 0
        res[tx] = res[tx]+1
    return res

erc20transfer_events = load("./v1_erc20transfer_events.json")
#(tx_hash,block,sender,receiver,amount)
transfer_events = load("./v1_transfer_events.json")
#(tx_hash,block,sender,receiver,token_id)
swap_events = load("./v1_swap_events.json")
#(tx_hash,block,sender,receiver,emerald_amount,eth_amount)

erc20transfer_ledger = load("./v1_erc20transfer_ledger.json")
#address:(input_tx_count, output_tx_count, amount_in, amount_out, balance, [tx_list], [recievedFrom])
transfer_ledger = load("./v1_transfer_ledger.json")
#address:(input_tx_count, output_tx_count, balance, [tx_list], [inbound_txs], [outbound_txs])
swap_ledger = load("./v1_swap_ledger.json")
#address:(emerald_bought, emerald_sold, ether_bought, ether_sold, emerald_received, eth_received, [tx_list], [received_from])
os_swaps = parse_os("./v1_os_events.json")
#address:(eth_spent, eth_gained, emeralds_bought, emeralds_sold, [tx_list])

correlations = csv_reader("./v1_correlation.csv")

addresses = set(erc20transfer_ledger.keys()).union(transfer_ledger.keys()).union(swap_ledger.keys()).union(os_swaps.keys())
print(f"Total addresses {len(addresses)}")

headers = ["address","emerald_balance","eth_balance","erc20_input_tx_count","erc20_output_tx_count","erc20_amount_in",
            "erc20_amount_out","erc20_balance","transfer_input_tx_count","transfer_output_tx_count",
            "transfer_output_balance","swap_ledger_emerald_bought","swap_ledger_emerald_sold",
            "swap_ledger_ether_gained","swap_ledger_ether_spent","swap_ledger_emerald_received",
            "swap_ledger_eth_received","swap_ledger_tx_list","swap_ledger_received_from",
            "os_eth_spent","os_eth_gained", "os_emeralds_bought","os_emeralds_sold","os_txs","is_contract"]
correlation = {}
for cr in correlations:
    correlation[cr[0]]= dictify(cr) 
del correlation["addresses"]

contracts = set()
for adr in correlation:
    if(correlation[adr]["is_contract"]=="True"):
        contracts.add(adr)
contracts.add("0x000000000000000000000000000000000000dEaD")
contracts.add("0x0000000000000000000000000000000000000000")

#get all opensea transactions
os_swaps_txs = list()
for adr in correlation:
    os_swaps_txs = os_swaps_txs + (correlation[adr]["os_txs"].split(', '))
os_swaps_txs = set(os_swaps_txs)
os_swaps_txs = [tx.lower() for tx in os_swaps_txs]
#build tx_hash : set(addresses dictionary)
tx_addresses = dict()

for ev in erc20transfer_events:
    tx = ev[0]
    sender = ev[2]
    receiver = ev[3]
    if(sender == receiver):
        continue
    txa = tx_addresses.get("address", set())
    if(sender not in contracts):
        txa.add(sender) 
    if(receiver not in contracts):
        txa.add(receiver) 
    if(txa != set()):
        tx_addresses[tx] = txa
for ev in transfer_events:
    tx = ev[0]
    if(tx in os_swaps_txs):
        continue
    sender = ev[2]
    receiver = ev[3]
    if(sender == receiver):
        continue
    txa = tx_addresses.get("address", set())
    if(sender not in contracts):
        txa.add(sender) 
    if(receiver not in contracts):
        txa.add(receiver) 
    if(txa != set()):
        tx_addresses[tx] = txa  
_clusters = []
for k in tx_addresses:
    rel_addresses = tx_addresses[k]    
    #print(rel_addresses) 
    found = False
    for adr in rel_addresses:
        for id in range(len(_clusters)):
            if (adr in _clusters[id]):
                _clusters[id] = _clusters[id].union(rel_addresses)
                found = True
                break
        if(found):
            break
    if(not found):
        _clusters.append(rel_addresses)
 
clusters = [cl for cl in _clusters if len(cl) > 1]

addresses_with_loss = []
total_loss = 0
paperhanded_loss = 0
cost_based_loss = 0
for adr in correlation:
    cr = correlation[adr]
    if(float(cr["emerald_balance"])>0):
        #JUST IF THERES ETH LOSS
        if(float(cr["eth_balance"])<0):
            eth_spent = float(cr["os_eth_spent"]) +  float(cr["swap_ledger_ether_spent"]) 
            eth_gained = float(cr["os_eth_gained"]) +  float(cr["swap_ledger_ether_gained"]) 
            emeralds_obtained =  float(cr["os_emeralds_bought"]) +  float(cr["swap_ledger_emerald_bought"])
            addresses_with_loss.append(adr)
            total_loss += float(cr["eth_balance"])
            paperhanded_loss += eth_gained - eth_spent
        # COST BASED LOSS
        # min(eth_spent,    
        if(float(cr["eth_balance"])<0):
            emeralds_obtained =  float(cr["os_emeralds_bought"]) +  float(cr["swap_ledger_emerald_bought"])
            eth_spent = float(cr["os_eth_spent"]) +  float(cr["swap_ledger_ether_spent"]) 
            avg_price = eth_spent / emeralds_obtained
            current_debt = -float(cr["emerald_balance"])*avg_price
            cost_based_loss += max(current_debt,float(cr["eth_balance"]))

print(f"Total PAPER loss: {paperhanded_loss}") 
print(f"Total COST BASED loss: {cost_based_loss}") 

clustered_correlation = {}
for addr in correlation:
    found = False
    for i in range(len(clusters)):
        if(addr in clusters[i]):
            found = True
            #if this cluster hasnt been added yet
            if(clustered_correlation.get(i,0) == 0):
                emerald_balance = 0
                eth_balance = 0
                os_eth_spent = 0
                swap_ledger_ether_spent = 0
                os_emeralds_bought = 0
                swap_ledger_emerald_bought = 0
                addresses = []
                for ad in clusters[i]:
                    emerald_balance += float(correlation[ad]["emerald_balance"])
                    eth_balance += float(correlation[ad]["eth_balance"])
                    os_eth_spent += float(correlation[ad]["os_eth_spent"])
                    swap_ledger_ether_spent += float(correlation[ad]["swap_ledger_ether_spent"])
                    os_emeralds_bought += float(correlation[ad]["os_emeralds_bought"])
                    swap_ledger_emerald_bought += float(correlation[ad]["swap_ledger_emerald_bought"])  
                clustered_correlation[i] = {
                    "emerald_balance":emerald_balance,
                    "eth_balance":eth_balance,
                    "os_eth_spent":os_eth_spent,
                    "swap_ledger_ether_spent":swap_ledger_ether_spent,
                    "os_emeralds_bought":os_emeralds_bought,
                    "swap_ledger_emerald_bought":swap_ledger_emerald_bought,
                    "clustered_addresses":addresses
                }  
    if(not found):
        clustered_correlation[addr] = correlation[addr]

print(f"Total addresses clustered {len(clustered_correlation.keys())}")

total_loss = 0
paperhanded_loss = 0
cost_based_loss = 0
for adr in clustered_correlation:
    cr = clustered_correlation[adr]
    if(float(cr["emerald_balance"])>0):
        #JUST IF THERES ETH LOSS
        if(float(cr["eth_balance"])<0):
            eth_spent = float(cr["os_eth_spent"]) +  float(cr["swap_ledger_ether_spent"])  
            emeralds_obtained =  float(cr["os_emeralds_bought"]) +  float(cr["swap_ledger_emerald_bought"])
            addresses_with_loss.append(adr)
            total_loss += float(cr["eth_balance"])
            paperhanded_loss += float(cr["eth_balance"])
        # COST BASED LOSS
        # min(eth_spent,    
        if(float(cr["eth_balance"])<0):
            emeralds_obtained =  float(cr["os_emeralds_bought"]) +  float(cr["swap_ledger_emerald_bought"])
            eth_spent = float(cr["os_eth_spent"]) +  float(cr["swap_ledger_ether_spent"]) 
            avg_price = eth_spent / emeralds_obtained
            current_debt = -float(cr["emerald_balance"])*avg_price
            cost_based_loss += max(current_debt,float(cr["eth_balance"]))
            
print(f"Total clustered PAPER loss: {paperhanded_loss}") 
print(f"Total clustered COST BASED loss: {cost_based_loss}") 