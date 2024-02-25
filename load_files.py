def load(file_path):
    try:
        with open(file_path, 'r') as file: 
            content = file.read() 
            loaded_list = eval(content)
            return loaded_list 
    except Exception as e:
        print(f"Exception{e}")
        return None

# ERC 20 v1
file_path = 'v1_erc20_txs.txt'  
v1_erc20_txs = load(file_path)
if v1_erc20_txs is not None:
    print("v1_erc20_txs: ", len(set(v1_erc20_txs)))


# ERC 20 v1
file_path = 'v1_erc721_txs.txt'  
v1_erc721_txs = load(file_path)
if v1_erc721_txs is not None: 
    print("v1_erc721_txs: ", len(set(v1_erc721_txs)))