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

clusters = []
for event in erc20transfer_events:
    sender = event[2]
    receiver = event[3]
    found = False
    if(sender in contracts or receiver in contracts):
        continue
    if(sender == receiver):
        continue
    for cl in clusters:
        if(sender in cl):
            found = True
            cl.add(receiver)
        elif(receiver in cl):
            found = True
            cl.add(sender)
    if(not found):
        clusters.append(set([sender,receiver]))


for event in transfer_events:
    tx_hash = event[0]
    sender = event[2]
    receiver = event[3]
    if(tx_hash in correlation[sender]["os_txs"]):
        continue
    found = False
    if(sender in contracts):
        continue
    if(receiver in contracts):
        continue
    if(sender == receiver):
        continue
    for cl in clusters:
        if(sender in cl):
            found = True
            cl.add(receiver)
        elif(receiver in cl):
            found = True
            cl.add(sender)
    if(not found):
        clusters.append(set([sender,receiver]))

total_eth_lost = 0
for adr in correlation:
    eth_balance = float(correlation[adr]["eth_balance"])
    if(float(correlation[adr]["emerald_balance"])<=0):
        continue
    if(float(correlation[adr]["eth_balance"])<0):
        total_eth_lost += eth_balance
    else:
        for cl in clusters:
            if(adr in cl):
                total_eth_lost += eth_balance
print(f"Total ETH lost {total_eth_lost}")

