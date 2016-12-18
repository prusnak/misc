#!/usr/bin/python
from __future__ import print_function
import sys
import requests
from bip32utils import BIP32Key
from operator import attrgetter
from decimal import Decimal


class Blockchain(object):

    api_uri = 'https://insight.bitpay.com/api'

    @classmethod
    def get_address_info(cls, addr):
        r = requests.get('%s/addr/%s' % (cls.api_uri, addr))
        return r.json()

    @classmethod
    def get_transaction_info(cls, tx):
        r = requests.get('%s/tx/%s' % (cls.api_uri, tx))
        return r.json()


class Address(object):

    def __init__(self):
        self.desc = ''
        self.address = ''
        self.balance = 0
        self.unconfirmed_balance = 0

    def fmt(self):
        return '%s %s %d %d' % (self.desc, self.address, self.balance, self.unconfirmed_balance)


class Transaction(object):

    def __init__(self):
        self.conf = 0
        self.tx_id = ''
        self.balance = 0

    def fmt(self):
        return '%d %s %d' % (self.conf, self.tx_id, self.balance)


class Account(object):

    def __init__(self, xpub):
        self.addresses = []
        self.transactions = []
        self.gap = 10
        self.acc_node = BIP32Key.fromExtendedKey(xpub)
        self.ext_node = self.acc_node.ChildKey(0)
        self.int_node = self.acc_node.ChildKey(1)

    def process(self):
        self.process_chain('m/0/', self.ext_node)
        self.process_chain('m/1/', self.int_node)
        self.transactions = [ self.process_transaction(x) for x in self.transactions ]
        self.transactions = sorted(self.transactions, key=attrgetter('conf'))

    def process_chain(self, desc, chain_node):
        i = 0
        g = 0
        while True:
            desci = '%s%d' % (desc, i)
            addr_node = chain_node.ChildKey(i)
            address = addr_node.Address()
            if self.process_address(desci, address):
                g = 0
            else:
                g += 1
            if g > self.gap:
                break
            i += 1

    def process_address(self, desc, address):
        j = Blockchain.get_address_info(address)
        n_tx = len(j['transactions'])

        a = Address()
        a.desc = desc
        a.address = str(j['addrStr'])
        a.balance = int(j['balanceSat'])
        a.unconfirmed_balance = int(j['unconfirmedBalanceSat'])
        self.addresses.append(a)

        for txid in j['transactions']:
            if txid in [ x.tx_id for x in self.transactions ]:
                continue
            t = Transaction()
            t.tx_id = txid
            self.transactions.append(t)

        return n_tx > 0

    def process_transaction(self, tx):
        j = Blockchain.get_transaction_info(tx.tx_id)
        bal = 0
        # analysis of inputs will probably break for coinbase transactions
        for i in j['vin']:
            if str(i['addr']) in [ x.address for x in self.addresses ]:
                bal -= int(i['valueSat'])
        # analysis of outputs will probably break for special (i.e. not pay-to-pubkey-hash) transactions
        for o in j['vout']:
            if str(o['scriptPubKey']['addresses'][0]) in [ x.address for x in self.addresses ]:
                bal += int(Decimal(o['value']) * 100000000) # ugly hack for missing valueSat :-(
        tx.conf = int(j['confirmations'])
        tx.balance = bal
        return tx


xpub = sys.argv[1]

acc = Account(xpub)
acc.process()

print('addresses:')
for a in acc.addresses:
    print(a.fmt())

print('transactions:')
for t in acc.transactions:
    print (t.fmt())
