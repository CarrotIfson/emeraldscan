mp_event_tx_scrapper_v1.py
  Iterates over blocks to dump a list of distinct tx where ERC20Transfer and Transfer events were emited
  outputs:
    v1_erc20_txs.txt
    v1_erc721_txs.txt

mp_ledger_erc20_v1.py
  Iterate over blocks to build a dictionary based ledger using ERC20Transfer events.
  outputs:
    v1_event_erc20_ledger.txt
  BROKEN FOR:
    0x75365dDb02bc316748fB9A2dc5a33B42f1fBA2E7 and 0x0B2680ED2EF5202c686Af9FdD996Ab7F857eCCe3