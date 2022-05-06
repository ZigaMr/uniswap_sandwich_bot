# uniswap_sandwich_bot
An old (june 2021) sandwich bot written in python. None of it still works and I have yet to push the deployment scripts and py envir requrements,
but hopefully someone finds it useful. 

It uses a slightly modified web3-flashbots library which at the time didn't allow to call local mev-geth instance. 
It utilizes sqlite db to dynamically parse "competitor" bots which might target the same sandwich opportunities so we can later analyze their transactions.

The bot was started by running blocknative_bot_async.py, but first we need to deploy the contract swawp_yul_prod.sol (working on deployment scripts).
Since london fork eip 1559 gas tokens which are minted and self-destroyed in the contract, aren't useful anymore (no gas refund). 
So please don't run the bot in production without modifing it first.
