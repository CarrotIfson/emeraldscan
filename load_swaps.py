def load(file_path):
    try:
        with open(file_path, 'r') as file: 
            content = file.read() 
            loaded_list = eval(content)
            return loaded_list 
    except Exception as e:
        print(f"Exception{e}")
        return None

# univ3 swaps
file_path = 'swaps.txt'  
swaps = load(file_path)
print("swaps: ", len(swaps))

addr_balance = {}
for s in swaps:
    spender = s[0]
    receiver = s[1]
    emerald_balance = s[2]
    eth_balance = s[3]
    
    if spender not in addr_balance:
        addr_balance[spender] = (0,0)
    
    addr_balance[spender] = (addr_balance[spender][0]-emerald_balance,addr_balance[spender][1]-eth_balance)

import json
with open("./v1_uni_swap_balances.json", "w") as file:
    json.dump(addr_balance, file)