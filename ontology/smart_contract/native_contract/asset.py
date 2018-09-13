#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import binascii
from time import time

from ontology.utils import util
from ontology.common.define import *
from ontology.common.address import Address
from ontology.account.account import Account
from ontology.common.error_code import ErrorCode
from ontology.core.transaction import Transaction
from ontology.exception.exception import SDKException
from ontology.vm.build_vm import build_native_invoke_code


class Asset(object):
    def __init__(self, sdk):
        self.__sdk = sdk

    @staticmethod
    def get_asset_address(asset: str) -> bytearray:
        """
        This interface is used to get the ONT or ONG asset's address.

        :param asset: a string which is used to indicate which asset's address we want to get.
        :return: asset's adress in the form of bytearray.
        """
        if asset.upper() == 'ONT':
            contract_address = ONT_CONTRACT_ADDRESS
        elif asset.upper() == 'ONG':
            contract_address = ONG_CONTRACT_ADDRESS
        else:
            raise ValueError("asset is not equal to ONT or ONG")
        return contract_address

    def query_balance(self, asset: str, b58_address: str) -> int:
        """
        This interface is used to query the account's ONT or ONG balance.

        :param asset: a string which is used to indicate which asset we want to check the balance.
        :param b58_address: a base58 encode account address.
        :return: account balance.
        """
        raw_address = Address.b58decode(b58_address).to_array()
        contract_address = util.get_asset_address(asset)
        invoke_code = build_native_invoke_code(contract_address, bytes([0]), "balanceOf", raw_address)
        unix_time_now = int(time())
        payer = Address(ZERO_ADDRESS).to_array()
        version = 0
        tx_type = 0xd1
        gas_price = 0
        gas_limit = 0
        attributes = bytearray()
        signers = list()
        hash_value = bytearray()
        tx = Transaction(version, tx_type, unix_time_now, gas_price, gas_limit, payer, invoke_code, attributes, signers,
                         hash_value)
        balance = self.__sdk.rpc.send_raw_transaction_pre_exec(tx)
        array = bytearray(binascii.a2b_hex(balance.encode('ascii')))
        array.reverse()
        try:
            balance = int(binascii.b2a_hex(array).decode('ascii'), 16)
        except ValueError:
            balance = 0
        return balance

    def query_allowance(self, asset: str, b58_from_address: str, b58_to_address: str) -> int:
        """

        :param asset: a string which is used to indicate which asset's allowance we want to get.
        :param b58_from_address: a base58 encode address which indicate where the allowance from.
        :param b58_to_address: a base58 encode address which indicate where the allowance to.
        :return: the amount of allowance in the from of int.
        """
        contract_address = util.get_asset_address(asset)
        raw_from = Address.b58decode(b58_from_address).to_array()
        raw_to = Address.b58decode(b58_to_address).to_array()
        args = {"from": raw_from, "to": raw_to}
        invoke_code = build_native_invoke_code(contract_address, bytes([0]), "allowance", args)
        unix_time_now = int(time())
        payer = Address(ZERO_ADDRESS).to_array()
        version = 0
        tx_type = 0xd1
        gas_price = 0
        gas_limit = 0
        attributes = bytearray()
        signers = list()
        hash_value = bytearray()
        tx = Transaction(version, tx_type, unix_time_now, gas_price, gas_limit, payer, invoke_code, attributes, signers,
                         hash_value)
        allowance = self.__sdk.rpc.send_raw_transaction_pre_exec(tx)
        array = bytearray(binascii.a2b_hex(allowance.encode('ascii')))
        array.reverse()
        try:
            allowance = int(binascii.b2a_hex(array).decode('ascii'), 16)
        except ValueError:
            allowance = 0
        return allowance

    @staticmethod
    def new_transfer_transaction(asset: str, b58_from_address: str, b58_to_address: str, amount: int,
                                 b58_payer_address: str,
                                 gas_limit: int, gas_price: int) -> Transaction:
        """
        This interface is used to generate a Transaction for transfer.

        :param asset: a string which is used to indicate which asset we want to transfer.
        :param b58_from_address: a base58 encode address which indicate where the asset from.
        :param b58_to_address: a base58 encode address which indicate where the asset to.
        :param amount: the amount of asset that will be transferred.
        :param b58_payer_address: a base58 encode address which indicate who will pay for the transaction.
        :param gas_limit: an int value that indicate the gas limit.
        :param gas_price: an int value that indicate the gas price.
        :return: a Transaction object which can be used for transfer.
        """
        contract_address = util.get_asset_address(asset)
        raw_from = Address.b58decode(b58_from_address).to_array()
        raw_to = Address.b58decode(b58_to_address).to_array()
        raw_payer = Address.b58decode(b58_payer_address).to_array()
        state = [{"from": raw_from, "to": raw_to, "amount": amount}]
        invoke_code = build_native_invoke_code(contract_address, bytes([0]), "transfer", state)
        unix_time_now = int(time())
        version = 0
        tx_type = 0xd1
        attributes = bytearray()
        signers = list()
        hash_value = bytearray()
        return Transaction(version, tx_type, unix_time_now, gas_price, gas_limit, raw_payer, invoke_code, attributes,
                           signers, hash_value)

    def send_transfer(self, asset: str, from_acct: Account, to_address: str, amount: int, payer: Account,
                      gas_limit: int, gas_price: int):
        tx = Asset.new_transfer_transaction(asset, from_acct.get_address_base58(), to_address, amount,
                                            payer.get_address_base58(),
                                            gas_limit, gas_price)
        self.__sdk.sign_transaction(tx, from_acct)
        if from_acct.get_address_base58() != payer.get_address_base58():
            self.__sdk.add_sign_transaction(tx, payer)
        return self.__sdk.rpc.send_raw_transaction(tx)

    def unbound_ong(self, base58_address: str) -> str:
        contract_address = util.get_asset_address("ont")
        return self.__sdk.rpc.get_allowance("ong", Address(contract_address).b58encode(), base58_address)

    def query_name(self, asset: str) -> str:
        """
        This interface is used to query the asset's name of ONT or ONG.

        :param asset: a string which is used to indicate which asset's name we want to get.
        :return: asset's name in the form of string.
        """
        contract_address = util.get_asset_address(asset)
        method = 'name'
        invoke_code = build_native_invoke_code(contract_address, bytes([0]), method, bytearray())
        unix_time_now = int(time())
        payer = Address(ZERO_ADDRESS).to_array()
        version = 0
        tx_type = 0xd1
        gas_price = 0
        gas_limit = 0
        attributes = bytearray()
        signers = list()
        hash_value = bytearray()
        tx = Transaction(version, tx_type, unix_time_now, gas_price, gas_limit, payer, invoke_code, attributes, signers,
                         hash_value)
        res = self.__sdk.rpc.send_raw_transaction_pre_exec(tx)
        return bytes.fromhex(res).decode()

    def query_symbol(self, asset: str) -> str:
        """
        This interface is used to query the asset's symbol of ONT or ONG.

        :param asset: a string which is used to indicate which asset's symbol we want to get.
        :return: asset's symbol in the form of string.
        """
        contract_address = util.get_asset_address(asset)
        method = 'symbol'
        invoke_code = build_native_invoke_code(contract_address, bytes([0]), method, bytearray())
        unix_time_now = int(time())
        payer = Address(ZERO_ADDRESS).to_array()
        version = 0
        tx_type = 0xd1
        gas_price = 0
        gas_limit = 0
        attributes = bytearray()
        signers = list()
        hash_value = bytearray()
        tx = Transaction(version, tx_type, unix_time_now, gas_price, gas_limit, payer, invoke_code, attributes, signers,
                         hash_value)
        res = self.__sdk.rpc.send_raw_transaction_pre_exec(tx)
        return bytes.fromhex(res).decode()

    def query_decimals(self, asset: str) -> int:
        """
        This interface is used to query the asset's decimals of ONT or ONG.

        :param asset: a string which is used to indicate which asset's decimals we want to get
        :return: asset's decimals in the form of int
        """
        contract_address = util.get_asset_address(asset)
        method = 'decimals'
        invoke_code = build_native_invoke_code(contract_address, bytes([0]), method, bytearray())
        unix_time_now = int(time())
        payer = Address(ZERO_ADDRESS).to_array()
        version = 0
        tx_type = 0xd1
        gas_price = 0
        gas_limit = 0
        attributes = bytearray()
        signers = list()
        hash_value = bytearray()
        tx = Transaction(version, tx_type, unix_time_now, gas_price, gas_limit, payer, invoke_code, attributes, signers,
                         hash_value)
        decimal = self.__sdk.rpc.send_raw_transaction_pre_exec(tx)
        return int(decimal)

    @staticmethod
    def new_withdraw_ong_transaction(claimer_addr: str, recv_addr: str, amount: int, payer_addr: str,
                                     gas_limit: int, gas_price: int) -> Transaction:
        ont_contract_address = util.get_asset_address("ont")
        ong_contract_address = util.get_asset_address("ong")
        args = {"sender": Address.b58decode(claimer_addr).to_array(), "from": ont_contract_address,
                "to": Address.b58decode(recv_addr).to_array(),
                "value": amount}
        invoke_code = build_native_invoke_code(ong_contract_address, bytes([0]), "transferFrom", args)
        unix_time_now = int(time())
        return Transaction(0, 0xd1, unix_time_now, gas_price, gas_limit, Address.b58decode(payer_addr).to_array(),
                           invoke_code,
                           bytearray(), [], bytearray())

    def send_withdraw_ong_transaction(self, claimer: Account, b58_recv_address: str, amount: int, payer: Account,
                                      gas_limit: int, gas_price: int) -> str:
        """
        This interface is used to withdraw a amount of ong and transfer them to receive address.

        :param claimer: the owner of ong that remained to claim.
        :param b58_recv_address: the address that received the ong.
        :param amount: the amount of ong want to claim.
        :param payer: indicate who will pay for the transaction.
        :param gas_limit: an int value that indicate the gas limit.
        :param gas_price: an int value that indicate the gas price.
        :return: hexadecimal transaction hash value.
        """
        b58_claimer = claimer.get_address_base58()
        b58_payer = payer.get_address_base58()
        tx = Asset.new_withdraw_ong_transaction(b58_claimer, b58_recv_address, amount, b58_payer, gas_limit, gas_price)
        tx = self.__sdk.sign_transaction(tx, claimer)
        if claimer.get_address_base58() != payer.get_address_base58():
            tx = self.__sdk.add_sign_transaction(tx, payer)
        self.__sdk.rpc.send_raw_transaction(tx)
        return tx.hash256_explorer()

    @staticmethod
    def new_approve(asset: str, send_address: str, recv_address: str, amount: int, payer: str, gas_limit: int,
                    gas_price: int) -> Transaction:
        contract_address = util.get_asset_address(asset)
        raw_send = Address.b58decode(send_address).to_array()
        raw_recv = Address.b58decode(recv_address).to_array()
        raw_payer = Address.b58decode(payer).to_array()
        args = {"from": raw_send, "to": raw_recv, "amount": amount}
        invoke_code = build_native_invoke_code(contract_address, bytes([0]), "approve", args)
        unix_time_now = int(time())
        return Transaction(0, 0xd1, unix_time_now, gas_price, gas_limit, raw_payer, invoke_code, bytearray(), [],
                           bytearray())

    def send_approve(self, asset, sender: Account, recv_addr: str, amount: int, payer: Account, gas_limit: int,
                     gas_price: int) -> str:
        b58_sender = sender.get_address_base58()
        b58_payer = payer.get_address_base58()
        tx = Asset.new_approve(asset, b58_sender, recv_addr, amount, b58_payer, gas_limit, gas_price)
        tx = self.__sdk.sign_transaction(tx, sender)
        if sender.get_address_base58() != payer.get_address_base58():
            tx = self.__sdk.add_sign_transaction(tx, payer)
        self.__sdk.rpc.send_raw_transaction(tx)
        return tx.hash256_explorer()

    @staticmethod
    def new_transfer_from(asset: str, send_addr: str, from_address: str, recv_addr: str, amount: int, payer: str,
                          gas_limit: int, gas_price: int) -> Transaction:
        raw_sender = Address.b58decode(send_addr).to_array()
        raw_from = Address.b58decode(from_address).to_array()
        raw_to = Address.b58decode(recv_addr).to_array()
        raw_payer = Address.b58decode(payer).to_array()
        contract_address = util.get_asset_address(asset)
        args = {"sender": raw_sender, "from": raw_from, "to": raw_to, "amount": amount}
        invoke_code = build_native_invoke_code(contract_address, bytes([0]), "transferFrom", args)
        unix_time_now = int(time())
        return Transaction(0, 0xd1, unix_time_now, gas_price, gas_limit, raw_payer, invoke_code, bytearray(), [],
                           bytearray())

    def send_transfer_from(self, asset: str, sender: Account, from_address: str, recv_address: str, amount: int,
                           payer: Account, gas_limit: int, gas_price: int) -> str:
        if sender is None or payer is None:
            raise SDKException(ErrorCode.param_err('parameters should not be null'))
        if amount <= 0 or gas_price < 0 or gas_limit < 0:
            raise SDKException(ErrorCode.param_error)
        b58_payer = payer.get_address_base58()
        b58_sender = sender.get_address_base58()
        tx = Asset.new_transfer_from(asset, b58_sender, from_address, recv_address, amount, b58_payer, gas_limit,
                                     gas_price)
        tx = self.__sdk.sign_transaction(tx, sender)
        if b58_sender != b58_payer:
            tx = self.__sdk.add_sign_transaction(tx, payer)
        self.__sdk.rpc.send_raw_transaction(tx)
        return tx.hash256_explorer()
