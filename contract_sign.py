import ast
from iconservice import *
from secp256k1 import PublicKey, ALL_FLAGS, NO_FLAGS, FLAG_VERIFY
TAG = 'ContractSign'


# An interface of ICON Token Standard, IRC-2
class TokenStandard(ABC):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def symbol(self) -> str:
        pass

    @abstractmethod
    def decimals(self) -> int:
        pass

    @abstractmethod
    def totalSupply(self) -> int:
        pass

    @abstractmethod
    def balanceOf(self, _owner: Address) -> int:
        pass

    @abstractmethod
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        pass


# An interface of tokenFallback.
# Receiving SCORE that has implemented this interface can handle
# the receiving or further routine.
class TokenFallbackInterface(InterfaceScore):
    @interface
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        pass


class ContractSign(IconScoreBase, TokenStandard):

    _BALANCES = 'balances'
    _TOTAL_SUPPLY = 'total_supply'
    _DECIMALS = 'decimals'

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._total_supply = VarDB(self._TOTAL_SUPPLY, db, value_type=int)
        self._decimals = VarDB(self._DECIMALS, db, value_type=int)
        self._balances = DictDB(self._BALANCES, db, value_type=int)

    def on_install(self, _initialSupply: int, _decimals: int) -> None:
        super().on_install()

        if _initialSupply < 0:
            revert("Initial supply cannot be less than zero")

        if _decimals < 0:
            revert("Decimals cannot be less than zero")
        if _decimals > 21:
            revert("Decimals cannot be more than 21")

        total_supply = _initialSupply * 10 ** _decimals
        Logger.debug(f'on_install: total_supply={total_supply}', TAG)

        self._total_supply.set(total_supply)
        self._decimals.set(_decimals)
        self._balances[self.msg.sender] = total_supply

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "ContractSign"

    @external(readonly=True)
    def symbol(self) -> str:
        return "BTC"

    @external(readonly=True)
    def decimals(self) -> int:
        return self._decimals.get()

    @external(readonly=True)
    def totalSupply(self) -> int:
        return self._total_supply.get()

    @external(readonly=True)
    def balanceOf(self, _owner: Address) -> int:
        return self._balances[_owner]

    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        if _data is None:
            _data = b'None'

        self._transfer(self.msg.sender, _to, _value, _data)

    def _transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):

        # Checks the sending value and balance.
        if _value < 0:
            revert("Transferring value cannot be less than zero")
        if self._balances[_from] < _value:
            revert(f"Out of balance !!! from : {_from} to: {_to} balance : {_value}")

        self._balances[_from] = self._balances[_from] - _value
        self._balances[_to] = self._balances[_to] + _value

        if _to.is_contract:
            # If the recipient is SCORE,
            #   then calls `tokenFallback` to hand over control.
            recipient_score = self.create_interface_score(_to, TokenFallbackInterface)
            recipient_score.tokenFallback(_from, _value, _data)

        # Emits an event log `Transfer`
        self.Transfer(_from, _to, _value, _data)
        Logger.debug(f'Transfer({_from}, {_to}, {_value}, {_data})', TAG)






    def _recover_key(self, msg_hash: bytes, signature: bytes, compressed: bool):
        _public_key = PublicKey(flags=ALL_FLAGS)

        if isinstance(msg_hash, bytes) and len(msg_hash) == 32 and isinstance(signature, bytes) and len(signature) == 65:
            internal_recover_sig = _public_key.ecdsa_recoverable_deserialize(
                ser_sig=signature[:64], rec_id=signature[64])
            internal_pubkey = _public_key.ecdsa_recover(
                msg_hash, internal_recover_sig, raw=True, digest=None)

            public_key = PublicKey(internal_pubkey, raw=False, ctx=_public_key.ctx)
            return public_key.serialize(compressed)

        return None

    @external
    def remotetx(self, _data: bytes = None) -> str:
        _conv_data = ast.literal_eval(_data.decode('utf-8'))
        msg_hash = sha3_256(_data)

        ##############################################################################
        signature = str.encode(_conv_data['signature'])

        vData = self._recover_key(msg_hash, signature, False)
        pubkey = PublicKey(vData, _conv_data, FLAG_VERIFY)

        #signature = pubkey.ecdsa_deserialize(signature)
        #isverify = pubkey.ecdsa_verify(msg_hash, signature, True)
        ##############################################################################


        _is_from = Address.from_string(_conv_data['data']['params']['_from'])
        _is_to = Address.from_string(_conv_data['data']['params']['_to'])
        _is_value = int(_conv_data['data']['params']['_value'], 16)

        self._transfer(_is_from, _is_to, _is_value, b'remote transaction')
        return "OKOK"

