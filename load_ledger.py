import json
def load_json_from_file(file_path):
    try:
        with open(file_path, 'r') as file:
            # Use the json.load() method to parse the JSON data from the file into a dictionary
            data = json.load(file)
            return data
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

file_path = 'v1_event_erc20_ledger.txt' 
erc20 = load_json_from_file(file_path)

file_path = 'v1_event_erc721_ledger.txt' 
erc721 = load_json_from_file(file_path)

addresses = set(erc20.keys()).union(erc721.keys())
enriched_ledger = {}

for a in addresses:
    enriched_ledger[a] = erc20.get(a,0) + erc721.get(a,0)*10**6
"""
#fix any erc20 balance
for k in erc20:
    if(erc20[k] < 0):
        erc20[k] += erc721[k]*10**6
    
#add addresses that only used erc721 to the ledger
for k in erc721:
    if(k not in erc20): 
        erc20[k] = erc721[k]*10**6
"""
with open("./v1_event_enriched_ledger.json", "w") as file:
    json.dump(enriched_ledger, file)

enriched_ledger_nz = {}
for k in enriched_ledger:
    if(enriched_ledger[k] != 0): 
        enriched_ledger_nz[k] = enriched_ledger[k]
with open("./v1_event_enriched_ledger_nonzero.json", "w") as file:
    json.dump(enriched_ledger, file)