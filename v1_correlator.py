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

def fmt(val):
    return float(format(val, ".4"))

erc20transfer_events = load("./v1_erc20transfer_events.json")
#(tx_hash,block,sender,receiver,amount)
transfer_events = load("./v1_transfer_events.json")
#(tx_hash,block,sender,receiver,token_id)
swap_events = load("./v1_swap_events.json")
#(tx_hash,block,sender,receiver,emerald_amount,eth_amount)

erc20transfer_ledger = load("./v1_erc20transfer_ledger.json")
#address:(input_tx_count, output_tx_count, amount_in, amount_out, balance, [tx_list])
transfer_ledger = load("./v1_transfer_ledger.json")
#address:(input_tx_count, output_tx_count, balance, [tx_list])
swap_ledger = load("./v1_swap_ledger.json")
#address:(emerald_bought, emerald_sold, ether_bought, ether_sold, emerald_received, eth_received, [tx_list])
os_swaps = parse_os("./v1_os_events.json")
#address:(eth_spent, eth_gained, emeralds_bought, emeralds_sold, [tx_list])

addresses = set(erc20transfer_ledger.keys()).union(transfer_ledger.keys()).union(swap_ledger.keys()).union(os_swaps.keys())
print(f"Total addresses {len(addresses)}")


correlation = [["addresses","emerald_balance","eth_balance","erc20_input_tx_count","erc20_output_tx_count","erc20_amount_in",
               "erc20_amount_out","erc20_balance","transfer_input_tx_count","transfer_output_tx_count",
               "transfer_output_balance","swap_ledger_emerald_bought","swap_ledger_emerald_sold",
               "swap_ledger_ether_gained","swap_ledger_ether_spent","swap_ledger_emerald_received",
               "swap_ledger_eth_received","swap_ledger_tx_list","os_eth_spent","os_eth_gained",
               "os_emeralds_bought","os_emeralds_sold"]]
for address in addresses:
    erc20_res = erc20transfer_ledger.get(address,(0,0,0,0,0,[]))
    erc20_input_tx_count = erc20_res[0]
    erc20_output_tx_count = erc20_res[1]
    erc20_amount_in = fmt(erc20_res[2] / 10**6)
    erc20_amount_out = fmt(erc20_res[3] / 10**6)
    erc20_balance = fmt(erc20_res[4] / 10**6)
    #erc20_tx_list = ', '.join(set(erc20_res[5]))
 
    transfer_res = transfer_ledger.get(address,(0,0,0,[]))
    transfer_input_tx_count = transfer_res[0]
    transfer_output_tx_count = transfer_res[1]
    transfer_output_balance = transfer_res[2]
    #transfer_tx_list = ', '.join(set(transfer_res[3]))
 
    swap_res = swap_ledger.get(address,(0,0,0,0,0,0,[]))
    swap_ledger_emerald_bought = fmt(swap_res[0] / 10**6)
    swap_ledger_emerald_sold = fmt(swap_res[1] / 10**6)
    swap_ledger_ether_bought = fmt(swap_res[2] / 10**18)
    swap_ledger_ether_sold = fmt(swap_res[3] / 10**18)
    swap_ledger_emerald_received = fmt(swap_res[4] / 10**6)
    swap_ledger_eth_received = fmt(swap_res[5] / 10**18)
    swap_ledger_tx_list = ', '.join(set(swap_res[6]))
 
    os_res = os_swaps.get(address, (0,0,0,0,[]))
    os_eth_spent = fmt(os_res[0] / 10**18)
    os_eth_gained = fmt(os_res[1] / 10**18)
    os_emeralds_bought = os_res[2]
    os_emeralds_sold = os_res[3]
    os_txs = ', '.join(set(os_res[4]))

    emerald_balance_agg = fmt(erc20_amount_in-erc20_amount_out+transfer_input_tx_count-transfer_output_tx_count)
    eth_balance = fmt(os_eth_gained - os_eth_spent + swap_ledger_ether_bought - swap_ledger_ether_sold)
    
    if(swap_ledger_ether_bought<0):
        print(f"Address {address}")
        print(f"BalanceERC20Trasnfer: in({erc20_amount_in}) out({erc20_amount_out}) : {erc20_amount_in-erc20_amount_out}")
        print(f"BalanceSwap = in({swap_ledger_emerald_bought}) out({swap_ledger_emerald_sold}) : {swap_ledger_emerald_bought-swap_ledger_emerald_sold}")
        print(f"Transfer = in({transfer_input_tx_count}) out({transfer_output_tx_count}): {transfer_input_tx_count-transfer_output_tx_count}")
        print(f"OSemerald = in({os_emeralds_bought}) out({os_emeralds_sold})")
        print(f"OverallBalance = {emerald_balance_agg}") 
        print(f"os_eth = {os_eth_gained} eth_spend = {os_eth_spent}") 
        print(f"swap_eth = {swap_ledger_ether_bought} swap_eth_spend = {swap_ledger_ether_sold}")
        print(f"eth_balance = {eth_balance}")
        print(f"txs = {swap_ledger_tx_list}")
    
    correlation.append([address, emerald_balance_agg, eth_balance, erc20_input_tx_count, erc20_output_tx_count, erc20_amount_in, erc20_amount_out, erc20_balance,
                        transfer_input_tx_count, transfer_output_tx_count, transfer_output_balance, swap_ledger_emerald_bought,
                        swap_ledger_emerald_sold, swap_ledger_ether_bought, swap_ledger_ether_sold, swap_ledger_emerald_received,
                        swap_ledger_eth_received, swap_ledger_tx_list, os_eth_spent, os_eth_gained, os_emeralds_bought, os_emeralds_sold,
                        os_txs])

import csv
with open("v1_correlation.csv", 'w', newline='') as csvfile:
    writer = csv.writer(csvfile, delimiter=';')
    writer.writerows(correlation)

