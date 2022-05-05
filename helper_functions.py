from web3.auto import w3
import json
import sqlite3 as sql
uniswap_address = w3.toChecksumAddress('0x7a250d5630b4cf539739df2c5dacb4c659f2488d')
uniswap_contract = w3.eth.contract(uniswap_address, abi=json.load(open('UniswapABI.json', 'r'))['abi'])

competition = [w3.toChecksumAddress('0x000000000000084e91743124a982076c59f10084'),
         w3.toChecksumAddress('0x00000000000064c443ef440577C26525A3C34A30'),
         w3.toChecksumAddress('0x00000000e8080dB3Ed60313725643D38beC42071'),
         w3.toChecksumAddress('0xC6E6dd6A0C61651d1bC055Dc1c22418a729d41Bb'),
         w3.toChecksumAddress('0xb5917A48a99C1f8C76119a5133fdE1169ec11170'),
         w3.toChecksumAddress('0x0d43d01c2262e1935c200ccac989af024269c07e'),
         w3.toChecksumAddress('0x0555bdebc3429585b4594285a76f853725a49532'),
         w3.toChecksumAddress('0xe34820500dcd2a2c3c4ce2c1cac561e30ede0dc7'),
         w3.toChecksumAddress('0x51acf0af77adcb20de482e1cd678f620baf07e0c'),
         w3.toChecksumAddress('0x0000000033431f236e97fa549b367827360effd7'),
         w3.toChecksumAddress('0x5b9cda9a39dccb8d5def007b72c6a969fd5bb267')]

addresses = [w3.toChecksumAddress('0xb6b7cc8c20a25d886f3feff988d15d267f71ac7c'),
             w3.toChecksumAddress('0x5b9cda9a39dccb8d5def007b72c6a969fd5bb267')]

def expected_return_fees(token_pool, weth_pool, value, fee=997, pct=1):
    return (value * fee * token_pool / (weth_pool * 1000 + value * fee))*pct

def get_acceptable_tokens(sql,
                          to='0xda1faeb056a2f568b138ca0ad9ad8a51915ba336',
                          from_='0xda1faeb056a2f568b138ca0ad9ad8a51915ba336',
                          fun=lambda x: '0x' + x[34:74]):
    import pandas as pd
    conn = sql.connect('etherscan_analysis/main_db.db')
    data = pd.read_sql('select * from transactions', conn)
    d = data[(data.to == to) | (data['from'] == from_)].copy()
    t = d.groupby('blockNumber').apply(lambda x: x.iloc[-1].value - x.iloc[0].value)
    t = t[t > 0]
    # return d.input.apply(fun).unique().tolist()
    return d[d.blockNumber.isin(t.index)].contractAddress.unique().tolist()



def get_acceptable_tokens_tx(sql,
                             to='0xda1faeb056a2f568b138ca0ad9ad8a51915ba336',
                             from_='0xda1faeb056a2f568b138ca0ad9ad8a51915ba336',
                             currency='WETH',
                             fun=lambda x: '0x' + x[34:74]):
    import pandas as pd
    conn = sql.connect('etherscan_analysis/main_db.db')
    data = pd.read_sql('select * from transactions', conn)
    print(len(data))
    d = data[(data.to == to) | (data['from'] == from_)].copy()
    t = d.groupby('blockNumber').apply(lambda x: pd.Series([x.iloc[-1].value - x.iloc[0].value, len(x), x.iloc[0].tokenSymbol]))
    t = t[(t[1] > 0) & (t[1] == 4) & (t[2] == currency)]
    # return d.input.apply(fun).unique().tolist()
    return d[d.blockNumber.isin(t.index)]

def get_blocks(from_, block_number, n):
    # importing the requests library
    import requests

    # api-endpoint
    URL = "https://blocks.flashbots.net/v1/blocks"
    # defining a params dict for the parameters to be sent to the API
    i = block_number
    while 'd' not in locals() and i < block_number+n:
        try:
            PARAMS = {'from': from_,
                      'block_number': i}

            # sending get request and saving the response as response object
            r = requests.get(url=URL, params=PARAMS)

            # extracting data in json format
            data = r.json()
            index = list(filter(lambda x: x['eoa_address'] == from_,
                                data['blocks'][0]['transactions']))[0]['bundle_index']
            # dict(map(lambda x: (x['total_miner_reward'], x['gas_used']),
            #          list(filter(lambda x: x['bundle_index'] == index, data['blocks'][0]['transactions']))))
            d = dict(map(lambda x: [int(x['total_miner_reward']), x['gas_used']],
                     list(filter(lambda x: x['bundle_index'] == index,
                                 data['blocks'][0]['transactions']))))
            print(i)
        except:
            i += 1
    if 'd' not in locals():
        return (False, False, False, False)
    print('Bundle len: ', len(d))
    return sum(d.keys()),\
           sum(d.values()),\
           data['blocks'][0]['miner'],\
           sum(d.keys())/sum(d.values())


def check_pct_token(contract_router="0x78d1866129ee81b8bc0a95bcbb2c633a6b80ebee",
                    start_block=None,
                    end_block=None):
    from etherscan_analysis.EtherScan import EtherScan
    from tests.ABIs import uniswap_pair_abi

    etherScan = EtherScan(w3.toChecksumAddress(contract_router),
                          'BEKN8SC2I4BRHXR6TGMATP7PRMVIBC4XYU',
                          db='main_db.db')
    if start_block == None or end_block == None:
        etherScan.get_transactions(endblock=str(w3.eth.blockNumber),
                                   startblock=str(w3.eth.blockNumber-10000),
                                   db_insert=False)
    else:
        etherScan.get_transactions(endblock=str(end_block),
                                   startblock=str(start_block),
                                   db_insert=False)

    contract = w3.eth.contract(w3.toChecksumAddress(contract_router), abi=uniswap_pair_abi)
    data = etherScan.pd_data.copy()
    data.value = data[['value', 'tokenDecimal']].apply(lambda x: x.value*10**x.tokenDecimal, 1)
    data2 = data[data.to == contract_router.lower()][
    ['blockNumber', 'hash', 'transactionIndex', 'contractAddress', 'value']]. \
    merge(data[data.to != contract_router.lower()][['hash', 'contractAddress', 'value']], on='hash')
    r = []
    s = 0
    for ind, i in enumerate(data2.blockNumber):
        if ind/len(data2) >= s:
            print(ind/len(data2))
            s += .1
        r.append(contract.functions.getReserves().call(block_identifier=i - 1))
    data2['reserves'] = r
    data2.contractAddress_x = data2.contractAddress_x.apply(w3.toChecksumAddress)
    data2.contractAddress_y = data2.contractAddress_y.apply(w3.toChecksumAddress)
    return data2.groupby('blockNumber').apply(token_pct_helper, contract=contract, first=contract.functions.token0().call())


def token_pct_helper(df, contract, first):
    # reserve0, reserve1, t = contract.functions.getReserves().call(block_identifier=df.blockNumber.iloc[0]-1)
    if df.contractAddress_x.iloc[0] == first:
        return df.value_y.iloc[0], expected_return_fees(df.reserves.iloc[0][1], df.reserves.iloc[0][0], df.value_x.iloc[0])
    else:
        return df.value_y.iloc[0], expected_return_fees(df.reserves.iloc[0][0], df.reserves.iloc[0][1], df.value_x.iloc[0])

def frontrun2(data, transaction_cache):
    tr_cache_temp = []  # Added temp cache to delete confirmed transactions from trans_cache
    for fr, tx in data['pending'].items():
        for i, t in tx.items():
            if not tx:
                continue
                print('Invalid tx')
            elif t[u'hash'] in transaction_cache:
                tr_cache_temp.append(t[u'hash'])
            else:
                if t[u'to'] == '0x00000000000064c443ef440577C26525A3C34A30':
                    print('Cunt front running')
                    print(t)
                handle_transaction(t)
                tr_cache_temp.append(t[u'hash'])
    transaction_cache = tr_cache_temp
    return len(data['pending']), transaction_cache


def handle_transaction(tx):
    if tx[u'blockHash'] != None:
        return

    gas_price = int(tx[u'gasPrice'], 16)
    one_gwei = int(1e9)
    my_gas_price = gas_price + one_gwei
    if triggers_buy(tx):
        # print('Front-running!!!')
        print()
        print(tx[u'hash'], int(tx[u'value'], 16) / 10 ** 18)
        method, params = uniswap_contract.decode_function_input(tx[u'input'])
        l = list(map(lambda x: contract_df[contract_df.token == x].name.iloc[0],
                     filter(lambda x: w3.toChecksumAddress(x) in contract_df.token.values, params['path'])))
        print(method.fn_name, l)
        if 'swapExact' in method.fn_name:
            print('AmountOutMin: ', params[u'amountOutMin'] / 10 ** 18)
        if method.fn_name in ['swapExactETHForTokens', 'swapExactTokensForETH', 'swapETHForExactTokens',
                              'swapTokensForExactETH']:
            print('Ratio: ', contracts[l[0]][1].call() / contracts[l[0]][0].call())
        print('Gas price: ', gas_price / 10 ** 9)


def triggers_buy(tx):
    if tx[u'to'] != uniswap_address:
        return False

    if tx['input'] == '0x':
        return False
    try:
        method, params = uniswap_contract.decode_function_input(tx[u'input'])
    except ValueError as e:
        print(e)
        pass
    except:
        pass
    return method.fn_name in ['swapExactETHForTokens',
                              'swapExactTokensForETH',
                              'swapETHForExactTokens',
                              'swapTokensForExactETH',
                              'swapExactTokensForTokens',
                              'swapTokensForExactTokens'
                              ] and any(map(lambda x: x in contract_df.token.values, params['path'])) \
           and int(tx[u'value'], 16) >= BUY_THRESHOLD

def from_private_key(private_key_bytes):
    import codecs
    import ecdsa
    from Crypto.Hash import keccak
    import os

    key = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1).verifying_key

    key_bytes = key.to_string()
    private_key = codecs.encode(private_key_bytes, 'hex')
    public_key = codecs.encode(key_bytes, 'hex')

    print("Private key: ", private_key)
    print("Public key: ", public_key)

    public_key_bytes = codecs.decode(public_key, 'hex')

    hash = keccak.new(digest_bits=256)
    hash.update(public_key_bytes)
    keccak_digest = hash.hexdigest()

    address = '0x' + keccak_digest[-40:]
    return address

def sha3(seed):
    from Crypto.Hash import keccak
    sha3_256 = lambda x: keccak.new(digest_bits=256, data=x).digest()
    return sha3_256(str(seed))

def normalize_address(x, allow_blank=False):
    from rlp.utils import decode_hex
    if allow_blank and x == '':
        return ''
    if len(x) in (42, 50) and x[:2] == '0x':
        x = x[2:]
    if len(x) in (40, 48):
        x = decode_hex(x)
    if len(x) == 24:
        assert len(x) == 24 and sha3(x[:20])[:4] == x[-4:]
        x = x[:20]
    if len(x) != 20:
        raise Exception("Invalid address format: %r" % x)
    return x

def mk_contract_address(sender, nonce):
    import rlp
    return sha3(rlp.encode([normalize_address(sender), nonce]))[12:]

def check_effective_gas():
    import pandas as pd
    import sqlite3 as sql
    conn = sql.connect('etherscan_analysis/main_db.db')
    data = pd.read_sql('select * from BundleData', conn)
    data['EffPriceIncluded'] = data[['TargetFromAddress', 'BlockTarget', 'NBlocks']].apply(lambda x: get_blocks(x[0], x[1], x[2]), 1)
    # data.EffPriceIncluded = data.EffPriceIncluded.apply(lambda x: (False, False, False) if x==False else x)
    data[['minerPayment', 'totalGas', 'minerAddress', 'EffPriceIncluded']] = pd.DataFrame(data.EffPriceIncluded.tolist(), index=data.index)
    # data.EffPriceIncluded = data.minerPayment.where(~data.minerPayment, data.minerPayment.div(data.totalGas))
    return data

# import time
#
# l = w3.eth.filter('latest')
#
# while True:
#     ts = time.time()
#     ll = l.get_new_entries()
#     for i in ll:
#         # print('===== Block hash:  ', i.hex())
#         block_hash = i.hex()
#         block = w3.eth.getBlock(block_hash, full_transactions=True)
#
#         for tx in transactions:
#             if tx[u'to'] in [w3.toChecksumAddress('0x00000000acd5ca17eee6d92d9ca121543126cce1'),
#                              w3.toChecksumAddress('0x8a69b34968aab824295e10b1c1fa49b453c0fada'),
#                              w3.toChecksumAddress('0xc6e6dd6a0c61651d1bc055dc1c22418a729d41bb'),
#                              w3.toChecksumAddress('0xb5917a48a99c1f8c76119a5133fde1169ec11170'),
#                              w3.toChecksumAddress('0x51acf0af77adcb20de482e1cd678f620baf07e0c')]:
#                 transactions = block['transactions']
#                 print('===== Block Number: ', block['number'])
#                 print(ts, '   From wallet: ', tx['from'])
#                 print(ts, '   Value ETH: ', tx['value'])

if __name__ == '__main__':
    import numpy as np
    # tokens = get_acceptable_tokens(sql,
    #                                '0x000000005736775feb0c8568e7dee77222a26880',
    #                                '0x000000005736775feb0c8568e7dee77222a26880')
    # tokens2 = get_acceptable_tokens(sql,
    #                                '0xda1faeb056a2f568b138ca0ad9ad8a51915ba336',
    #                                '0xda1faeb056a2f568b138ca0ad9ad8a51915ba336')
    # data = get_acceptable_tokens_tx(sql,
    #                                 '0x00000000b7ca7e12dcc72290d1fe47b2ef14c607',
    #                                 '0x00000000b7ca7e12dcc72290d1fe47b2ef14c607')
    # from tests.ABIs import uniswap_pair_abi
    # import pandas as pd
    # data = check_pct_token('0xd01a189b95d2b07600de7003d6122e843e27447b')

    # data = get_blocks(w3.toChecksumAddress('0x60fa342f253addbc138c899afd0957e2c2d4da3d'), 12866864)
    data = check_effective_gas()
    data['ratio'] = data.MyEfPrice.div(data.EffPriceIncluded.where(data.EffPriceIncluded != False, np.inf))