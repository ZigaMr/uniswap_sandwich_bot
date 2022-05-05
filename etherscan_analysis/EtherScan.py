import requests
import pandas as pd
from datetime import datetime
import sqlite3 as sql
import time
import numpy as np
#import pycoingecko
from web3 import Web3, HTTPProvider
w3 = Web3(HTTPProvider("<GETH URL>"))

class EtherScan:

    def __init__(self, contract_address: str, key, db=r'main_db.db', contract=False, network='etherscan',
                 token_address=None):
        self.contract_address = contract_address.lower()
        self.key = key
        if db:
            self.conn = sql.connect(db)
        self.contract = contract
        if contract:
            self.url_token = 'https://api.{network}/api?module=account&'.\
                                 format(network=network + '.io' if network=='etherscan' else network + '.com') + \
                             'action=txlist&' \
                             'address={}&' \
                             'page=1&' \
                             'offset={}&' \
                             '{}' \
                             '{}' \
                             'sort={}&' \
                             'apikey={}'
        else:
            self.url_token = 'https://api.{network}/api?module=account&'.\
                                 format(network=network + '.io' if network=='etherscan' else network + '.com') + \
                             'action=tokentx&' + \
                             'address={}&' + \
                             'contractaddress={}&'.format(token_address) + \
                             'page=1&' \
                             'offset={}&' \
                             '{}' \
                             '{}' \
                             'sort={}&' \
                             'apikey={}'



    def get_transactions(self, offset=10000, endblock='', startblock='', db_insert=True, threshold=None, dir='asc'):
        """
        Download all transactions for specific contract address
        :param endblock:
        :param startblock:
        :param db_insert:
        :return:
        """
        data = requests.get(self.url_token.format(self.contract_address,
                                                  offset,
                                                  'endblock={}&'.format(endblock),
                                                  'startblock={}&'.format(startblock),
                                                  dir,
                                                  self.key))
        self.pd_data = pd.DataFrame(data.json()['result'])
        # while len(self.pd_data) == 0:
        #     time.sleep(5)
        if self.pd_data.empty:
            return False
        self.pd_data.timeStamp = self.pd_data.timeStamp.apply(
            lambda x: datetime.utcfromtimestamp(int(x))).dt.tz_localize('UTC')
        if not self.contract:
            self.pd_data.value = self.pd_data[['value', 'tokenDecimal']].apply(
                lambda x: float(x[0][:-int(x[1])] + '.' + x[0][-int(x[1]):]),
                axis=1)
        else:
            self.pd_data['tokenDecimal'] = 0
        self.pd_data[['blockNumber', 'nonce', 'tokenDecimal', 'transactionIndex', 'gas', 'gasUsed',
                      'cumulativeGasUsed', 'confirmations']] = \
            self.pd_data[
                ['blockNumber', 'nonce', 'tokenDecimal', 'transactionIndex', 'gas', 'gasUsed',
                 'cumulativeGasUsed', 'confirmations']].astype(int)
        min_block, max_block = self.pd_data.blockNumber.min(), self.pd_data.blockNumber.max()
        if db_insert:
            # Only insert rows with new blockNumbers
            block_numbers = {i[0] for i in
                             self.conn.execute(
                                 'select distinct(blockNumber) from transactions where [to] = "{}" or [from] = "{}"'
                                 .format(self.contract_address, self.contract_address)).fetchall()}
            if threshold:
                data_to_insert = self.pd_data[
                    (~self.pd_data.blockNumber.isin(block_numbers)) & (self.pd_data.value >= threshold)]
            else:
                data_to_insert = self.pd_data[~self.pd_data.blockNumber.isin(block_numbers)]
            data_to_insert = data_to_insert[['blockHash',
                                            'blockNumber',
                                            'confirmations',
                                            'contractAddress',
                                            'cumulativeGasUsed',
                                            'from',
                                            'gas',
                                            'gasPrice',
                                            'gasUsed',
                                            'hash',
                                            'input',
                                            'nonce',
                                            'timeStamp',
                                            'to',
                                            'tokenDecimal',
                                            'transactionIndex',
                                            'value']]
            print('Api data len: {}'.format(self.pd_data.__len__()))
            print('Filtered data len: {}'.format(data_to_insert.__len__()))
            data_to_insert.to_sql('transactions', self.conn, index=False, if_exists='append')

        return min_block, max_block

    def get_all_transactions(self, threshold=None):
        endblock = None
        max_endblock, min_endblock = self.get_transactions(endblock=endblock if endblock else '', threshold=threshold)

        while len(self.pd_data) > 2:
            # endblock = self.conn.execute('select min(blockNumber) from transactions where contractAddress = "{}"'.
            #                              format(self.contract_address)).fetchall()[0][0]
            min_endblock, max_endblock = self.get_transactions(endblock=min_endblock if min_endblock else '',
                                                               threshold=threshold)
            new_transactions = len(self.pd_data[self.pd_data.value >= threshold])
            time.sleep(1)
            print(new_transactions)
            print(min_endblock)
            print(datetime.fromtimestamp(self.pd_data.timeStamp.min()))

    def get_block_txs(self, block):
        data = requests.get(self.url_token.format(self.contract_address,
                                                  offset,
                                                  'endblock={}&'.format(endblock),
                                                  'startblock={}&'.format(startblock),
                                                  dir,
                                                  self.key))

    def get_all_transactions_forward(self, threshold=None):
        new_transactions = 6
        while new_transactions > 1:
            startblock = self.conn.execute('select max(blockNumber) from transactions where [to] = "{}" or [from] = "{}"'.
                                           format(self.contract_address, self.contract_address)).fetchall()[0][0]
            b = self.get_transactions(startblock=startblock+1 if startblock else '', threshold=threshold)
            if not b:
                return
            new_transactions = len(self.pd_data)
            time.sleep(1)
            print(new_transactions)
            print(startblock)
            print(self.pd_data.timeStamp.min())

    def get_cunts_tokens(self, cunt_address):
        pass


    def read_data(self, query):
        data = self.conn.execute(query)
        data = pd.DataFrame(data=data.fetchall(), columns=[d[0] for d in data.description])
        if 'timeStamp' in data.columns:
            data.timeStamp = pd.to_datetime(data.timeStamp)
        return data

    def close_db(self):
        self.conn.close()

    @staticmethod
    def get_time_estimate(gas_price, key):
        url = 'https://api.etherscan.io/api?module=gastracker&action=gasestimate&gasprice={0}&apikey={1}'.format(gas_price, key)
        return requests.get(url).json()
    # def get_token_transactions(self, address, ):
    # def get_block(self, num):
    #     template_url = 'https://api.etherscan.io/api?module=proxy&action=eth_getBlockByNumber&tag=0x{block}&boolean=true&apikey={key}'
    #     data = requests.get(template_url.format(num, self.key))

class CoinGeckoAPI:
    def __init__(self):
        pass



if __name__ == '__main__':
    """
    ether = EtherScan(w3.toChecksumAddress('0x000000005736775feb0c8568e7dee77222a26880'),
                      'BEKN8SC2I4BRHXR6TGMATP7PRMVIBC4XYU',
                      db='main_db.db',
                      contract=True)
    ether.get_all_transactions_forward()

    ether = EtherScan(w3.toChecksumAddress('0xfad95B6089c53A0D1d861eabFaadd8901b0F8533'),
                      'BEKN8SC2I4BRHXR6TGMATP7PRMVIBC4XYU',
                      db='main_db.db',
                      contract=True)
    ether.get_all_transactions_forward()

    ether = EtherScan(w3.toChecksumAddress('0x00000000003b3cc22af3ae1eac0440bcee416b40'),
                      'BEKN8SC2I4BRHXR6TGMATP7PRMVIBC4XYU',
                      db='main_db.db',
                      contract=True)
    ether.get_all_transactions_forward()

    ether = EtherScan(w3.toChecksumAddress('0x000000000000cb53d776774284822b1298ade47f'),
                      'BEKN8SC2I4BRHXR6TGMATP7PRMVIBC4XYU',
                      db='main_db.db',
                      contract=True)
    ether.get_all_transactions_forward()

    ether = EtherScan(w3.toChecksumAddress('0x00000000b7ca7e12dcc72290d1fe47b2ef14c607'),
                      'BEKN8SC2I4BRHXR6TGMATP7PRMVIBC4XYU',
                      db='main_db.db',
                      contract=True)
    ether.get_all_transactions_forward()

    ether = EtherScan(w3.toChecksumAddress('0x0000000099cb7fc48a935bceb9f05bbae54e8987'),
                      'BEKN8SC2I4BRHXR6TGMATP7PRMVIBC4XYU',
                      db='main_db.db',
                      contract=True)
    ether.get_all_transactions_forward()
    """""
    ether = EtherScan(w3.toChecksumAddress('0xc9e2c9718fF7d3129B9Ac12168195507e4275Cea'),
                      'BEKN8SC2I4BRHXR6TGMATP7PRMVIBC4XYU',
                      db='main_db.db',
                      contract=True)
    ether.get_all_transactions_forward()
