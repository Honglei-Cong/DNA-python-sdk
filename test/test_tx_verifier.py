#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import unittest

from test import sdk


class TestMerkleVerifier(unittest.TestCase):
    def test_main_net(self):
        sdk.rpc.connect_to_main_net()
        try:
            block = sdk.rpc.get_block_by_height(0)
            for tx in block.get('Transactions', dict()):
                tx_hash = tx['Hash']
                result = sdk.service.tx_verifier().verify_by_tx_hash(tx_hash)
                self.assertTrue(result)
        finally:
            sdk.rpc.connect_to_test_net()

    def test_test_net(self):
        sdk.rpc.connect_to_test_net()
        block = sdk.rpc.get_block_by_height(0)
        for tx in block.get('Transactions', dict()):
            tx_hash = tx['Hash']
            result = sdk.service.tx_verifier().verify_by_tx_hash(tx_hash)
            self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()