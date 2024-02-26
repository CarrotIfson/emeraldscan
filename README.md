# V1 Emerald Scanner

mp_event_tx_scrapper_v1.py
> Iterates over the blocks to get all transactions where a ERC20Transfer or Transfer Event occured
> Outputs: 
- v1_erc20_txs.txt
- v1_erc721_txs.txt

mp_lerger_erc20_v1.py
> Iterates over the blocks to get build a ledger based on the ERC20Trasnfer events
> Outputs: 
- v1_event_erc20_ledger.txt

mp_lerger_erc721_v1.py
> Iterates over the blocks to get build a ledger based on the Trasnfer events
> Outputs: 
- v1_event_erc721_ledger.txt

load_dict_files.py
> Reads v1_event_erc20_ledger.txt and v1_event_erc721_ledger.txt to produce an "enriched ledger" combining the two previous ones,
> Outputs:
- v1_event_enriched_ledger.txt

mp_swap_event_tracker_v1.py
> Iterates over the blocks to get a list of univ3 swap events for emeralds
> Outputs:
- swaps.txt

load_swap_files.py
> Loads swaps.txt and generates a json with spender, emerald balance, eth balance as a result of the swaps. The Emerald and ETH balance doesnt take into account if the spender != receiver on the uniswap trasnaction
> Outputs:
- v1_uni_swap_balances.json

Note: the following addresses keep appearing as negative balance
0x75365dDb02bc316748fB9A2dc5a33B42f1fBA2E7
0x1095dAE2AAA97E9e6B8C4dc307333Ae64D3a13C6
0xb9467aa7E6636C719De9858EA589a579bae53899
0x0000000000000000000000000000000000000000

The following has also an inconsistent balance:
0x0B2680ED2EF5202c686Af9FdD996Ab7F857eCCe3


Validation through:
https://etherscan.io/balancecheck-tool
at block height 19141344 for the v1 contract: 0x1d2fc977cc1e1fbd57a8b7f81fcd5d541d8531dd
yields positive results for the rest of checked addresses