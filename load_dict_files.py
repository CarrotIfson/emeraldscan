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

#fix any erc20 balance
for k in erc20:
    if(erc20[k] < 0):
        erc20[k] += erc721[k]*10**6
    
#add addresses that only used erc721 to the ledger
for k in erc721:
    if(k not in erc20): 
        erc20[k] = erc721[k]


for k in erc20:
    if(erc20[k] < 0):
        print(k)

with open("./v1_event_enriched_ledger.txt", "w") as file:
    json.dump(erc20, file)
