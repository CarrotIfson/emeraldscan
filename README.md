# V1 Emerald Scanner

v1_emerald_transfer_events.py
> Iterates over the blocks an listen to Transfer events for the V1 contract
> Outputs: 
- v1_transfer_events.json 
(tx_hash,block,sender,receiver,token_id)
- v1_transfer_ledger.json
(in_tx_count, out_tx_count, balance)

v1_emerald_erc20transfer_events.py
> Iterates over the blocks an listen to erc20Transfer events for the V1 contract
> Outputs: 
- v1_erc20transfer_events.json 
(tx_hash,block,sender,receiver,amount)
- v1_erc20transfer_ledger.json 
(in_tx_count, out_tx_count, amount_in, amount_out, balance)

v1_emerald_swap_events.py
> Iterates over the blocks an listen to Uniswap SWAP events for the V1 contract
> Outputs: 
- v1_swap_events.json 
(tx_hash,block,sender,receiver,emerald_amount,eth_amount)
- v1_swap_ledger.json
(emerald_in, emerald_out, eth_in, eth_out, emerald_received, eth_received, tx_list)

v1_correlator.py
> Reads the ledger outputs and os_event files and combines them into a csv
> Outputs:
- v1_correlation.csv

Validation through:
https://etherscan.io/balancecheck-tool
at block height 19141344 for the v1 contract: 0x1d2fc977cc1e1fbd57a8b7f81fcd5d541d8531dd
yields positive results for the rest of checked addresses