from eth_account import Account
from eth_account.signers.local import LocalAccount
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from binascii import b2a_hex, a2b_hex


def create_wallet(extra = ""):
    acct = Account.create(extra_entropy=extra)
    return (acct.key.hex()[2:], acct.address)


def import_wallet(private_key):
    assert private_key is not None, "PRIVATE_KEY none"
    assert len(private_key) == 64, "Len must 32 bytes(64 hex chars)"
    assert "0x" not in private_key, "Private key do not start with 0x hex prefix"
    account: LocalAccount = Account.from_key(private_key)
    print(account.key.hex())
    assert account.key.hex()[2:] == private_key, "Import Wallet Err"
    return (account.key.hex()[2:], account.address)


def encrypt_wallet_key(private_key: str, aes_key: str):
    assert private_key is not None, "PRIVATE_KEY none"
    assert len(private_key) == 64, "Len must 32 bytes(64 hex chars)"
    assert "0x" not in private_key, "Private key do not start with 0x hex prefix"
    assert len(aes_key) <= 16, "aes_key must <= 16"

    private_key = a2b_hex(private_key)
    aes_key = aes_key.encode(encoding='utf8').rjust(16, b"\x00")
    # aes_key = a2b_hex(aes_key)
    cipher = AES.new(aes_key, AES.MODE_EAX)
    ciphertext: bytes = cipher.encrypt(private_key)
    return (ciphertext.hex(), cipher.nonce.hex())


def decrypt_wallet_key(ciphertext: bytes, aes_key: str, nonce: bytes):
    assert len(aes_key) <= 16, "aes_key > 16"
    aes_key = aes_key.encode(encoding='utf8').rjust(16, b"\x00")
    decrypt = AES.new(aes_key, AES.MODE_EAX, nonce)
    plain_text: bytes = decrypt.decrypt(ciphertext)
    return (plain_text.hex())
    

def test_de():
    data = b'\xff\x96\xef\x8d\xbe\xf6\x02\x81\x07\xdc\x85m\xa5e\xcb?:\xbfh\x19\xd5q-\xe2\x8d\x89\xc3\xedO\xceC\xdb'

    # key = '1234'.encode(encoding='utf8').rjust(16, b"\x00")
    key = a2b_hex('1234')
    print(key)
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext = cipher.encrypt(data)

    print(f'nonce: {cipher.nonce}')
    print(f'cipher: {b2a_hex(ciphertext)}')
    print(f'cipher: {a2b_hex(ciphertext.hex())}')

    # decrypt
    decrypt = AES.new(key, AES.MODE_EAX, cipher.nonce)
    plain_text = decrypt.decrypt(ciphertext)
    print(plain_text)


if __name__ == "__main__":
    # key,addr = create_wallet()
    # print(encrypt_wallet_key(key, '1234'))
    print(import_wallet('95bf73c2d345c6f70ea26d85515fd59f34b42a112b1456312667ab2dbb26fc72'))