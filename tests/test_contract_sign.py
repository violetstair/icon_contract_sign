import os
import ast
import json
import logging

from iconsdk.builder.transaction_builder import (
    DeployTransactionBuilder,
    CallTransactionBuilder,
)
from iconsdk.wallet.wallet import KeyWallet
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.icon_service import IconService
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction

from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS

DIR_PATH = os.path.abspath(os.path.dirname(__file__))


logging.getLogger('SIGN::POC:').setLevel(logging.DEBUG)

class TestContractSign(IconIntegrateTestBase):

    logger = logging.getLogger('SIGN::POC:')
    #TEST_HTTP_ENDPOINT_URI_V3 = "https://bicon.net.solidwallet.io/api/v3"
    TEST_HTTP_ENDPOINT_URI_V3 = 'http://127.0.0.1:9000/api/v3'
    SCORE_PROJECT = os.path.abspath(os.path.join(DIR_PATH, '..'))

    def setUp(self):
        super().setUp()

        self.icon_service = None
        # if you want to send request to network, uncomment next line
        self.icon_service = IconService(HTTPProvider(self.TEST_HTTP_ENDPOINT_URI_V3))

        # install SCORE
        self.initial_supply = 1
        self.decimals = 6
        params = {
            '_initialSupply': self.initial_supply,
            '_decimals': self.decimals
        }
        self._score_address = self._deploy_score(params=params)['scoreAddress']

    def _deploy_score(self, to: str = SCORE_INSTALL_ADDRESS, params: dict = None) -> dict:
        # Generates an instance of transaction for deploying SCORE.
        transaction = DeployTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(to) \
            .step_limit(100_000_000_000) \
            .nid(3) \
            .nonce(100) \
            .content_type("application/zip") \
            .content(gen_deploy_data_content(self.SCORE_PROJECT)) \
            .params(params) \
            .build()

        # Returns the signed transaction object having a signature
        signed_transaction = SignedTransaction(transaction, self._test1)

        # process the transaction
        tx_result = self.process_transaction(signed_transaction, self.icon_service)

        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])
        self.assertTrue('scoreAddress' in tx_result)

        return tx_result

    def test_score_update(self):
        # update SCORE
        tx_result = self._deploy_score(to=self._score_address)

        self.assertEqual(self._score_address, tx_result['scoreAddress'])

    def test_call_name(self):
        # Generates a call instance using the CallBuilder
        call = CallBuilder().from_(self._test1.get_address()) \
            .to(self._score_address) \
            .method("name") \
            .build()

        # Sends the call request
        response = self.process_call(call, self.icon_service)

        self.assertEqual("ContractSign", response)

    def test_call_symbol(self):
        # Generates a call instance using the CallBuilder
        call = CallBuilder().from_(self._test1.get_address()) \
            .to(self._score_address) \
            .method("symbol") \
            .build()

        # Sends the call request
        response = self.process_call(call, self.icon_service)

        self.assertEqual("BTC", response)

    def test_call_decimals(self):
        # Generates a call instance using the CallBuilder
        call = CallBuilder().from_(self._test1.get_address()) \
            .to(self._score_address) \
            .method("decimals") \
            .build()

        # Sends the call request
        response = self.process_call(call, self.icon_service)

        self.assertEqual(hex(self.decimals), response)

    def test_call_totalSupply(self):
        # Generates a call instance using the CallBuilder
        call = CallBuilder().from_(self._test1.get_address()) \
            .to(self._score_address) \
            .method("totalSupply") \
            .build()

        # Sends the call request
        response = self.process_call(call, self.icon_service)

        self.assertEqual(hex(self.initial_supply * 10 ** self.decimals), response)

    def test_call_balanceOf(self):
        # Make params of balanceOf method
        params = {
            # token owner
            '_owner': self._test1.get_address()
        }
        # Generates a call instance using the CallBuilder
        call = CallBuilder().from_(self._test1.get_address()) \
            .to(self._score_address) \
            .method("balanceOf") \
            .params(params) \
            .build()

        # Sends the call request
        response = self.process_call(call, self.icon_service)

        self.assertEqual(hex(self.initial_supply * 10 ** self.decimals), response)

    def _call_balance(self, addr: str) -> str:
        params = {
            '_owner': addr
        }
        # Generates a call instance using the CallBuilder
        call = CallBuilder().from_(addr) \
            .to(self._score_address) \
            .method('balanceOf') \
            .params(params) \
            .build()

        # Sends the call request
        request = self.process_call(call, self.icon_service)
        return request

    def test_token_transfer(self):
        # Make params of transfer method
        to = self._wallet_array[0].get_address()
        value = 100
        params = {
            '_to': to,
            '_value': value,
        }

        # Generates an instance of transaction for calling method in SCORE.
        transaction = CallTransactionBuilder() \
            .from_(self._test1.get_address()) \
            .to(self._score_address) \
            .step_limit(10_000_000) \
            .nid(3) \
            .nonce(100) \
            .method("transfer") \
            .params(params) \
            .build()

        # Returns the signed transaction object having a signature
        signed_transaction = SignedTransaction(transaction, self._test1)

        # Sends the transaction to the network
        tx_result = self.process_transaction(signed_transaction, self.icon_service)

        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

        # Sends the call balanceOf
        response = self._call_balance(to)

        # check balance of receiver
        self.assertEqual(hex(value), response)

    def _transfer_token(self, _from: KeyWallet, _to: KeyWallet, _statue: bool):
        value = 500
        params = {
            '_to': _to.get_address(),
            '_value': value,
        }

        transaction = CallTransactionBuilder() \
            .from_(_from.get_address()) \
            .to(self._score_address) \
            .step_limit(10_000_000) \
            .nid(3) \
            .nonce(100) \
            .method("transfer") \
            .params(params) \
            .build()

        signed_transaction = SignedTransaction(transaction, _from)

        tx_result = self.process_transaction(signed_transaction, self.icon_service)

        self.logger.debug('TX RESULT : %s' % tx_result)

        self.assertTrue('status' in tx_result)
        self.assertEqual(1, tx_result['status'])

        if _statue:
            response = self._call_balance(_to.get_address())
            self.assertEqual(hex(value), response)

    def test_transaction(self):
        self.logger.info('Start transfer transaction...')

        _user_wallet = self._wallet_array[1]
        _remote_wallet = self._wallet_array[2]
        _to = self._wallet_array[3]

        self._transfer_token(self._test1, _user_wallet, True)
        self._transfer_token(self._test1, _remote_wallet, True)
        self._transfer_token(self._test1, _to, True)
        #self._transfer_token(_remote_wallet, self._test1, False)

        response = self._call_balance(_user_wallet.get_address())
        self.logger.info("BALANCE [%s] : %s" % (_user_wallet.get_address(), int(response, 16)))
        response = self._call_balance(_remote_wallet.get_address())
        self.logger.info("BALANCE [%s] : %s" % (_remote_wallet.get_address(), int(response, 16)))
        response = self._call_balance(_to.get_address())
        self.logger.info("BALANCE [%s] : %s" % (_to.get_address(), int(response, 16)))


        self.logger.info('Token Transfer Transaction Build ...')
        value = 100
        params = {
            '_from': _user_wallet.get_address(),
            '_to': _to.get_address(),
            '_value': value
        }
        transaction = CallTransactionBuilder() \
            .from_(_user_wallet.get_address()) \
            .to(self._score_address) \
            .step_limit(10_000_000) \
            .nid(3) \
            .nonce(100) \
            .method("transfer") \
            .params(params) \
            .build()
        signedTransaction = SignedTransaction(transaction, _user_wallet)

        self.logger.info('Remote Excute Transaction Build ...')
        params = {
            '_data': f'{signedTransaction.signed_transaction_dict}'.encode()
        }
        transaction = CallTransactionBuilder() \
            .from_(_remote_wallet.get_address()) \
            .to(self._score_address) \
            .step_limit(10_000_000) \
            .nid(3) \
            .nonce(100) \
            .method("transaction") \
            .params(params) \
            .build()
        signed_transaction = SignedTransaction(transaction, _remote_wallet)

        self.logger.info('Excute Transaction ...')
        tx_result = self.process_transaction(signed_transaction, self.icon_service)

        self.logger.debug('TX RESULT : %s' % tx_result)

        response = self._call_balance(_user_wallet.get_address())
        self.logger.info("BALANCE [%s] : %s" % (_user_wallet.get_address(), int(response, 16)))
        response = self._call_balance(_remote_wallet.get_address())
        self.logger.info("BALANCE [%s] : %s" % (_remote_wallet.get_address(), int(response, 16)))
        response = self._call_balance(_to.get_address())
        self.logger.info("BALANCE [%s] : %s" % (_to.get_address(), int(response, 16)))

        self.assertEqual(200, int(response, 16))
