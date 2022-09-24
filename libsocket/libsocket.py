import os
import socket
from typing import Tuple

from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey

HEADER: int = 64
FILL_LENGTH_CHAR: str = "a"

def fill_length(length: str) -> str:
    """Fill the message containing the length of the message to fit in the header.

    Args:
        length (str): Actual length of the message (digit)

    Returns:
        str: Size of the message with the correct length
    """
    length_to_add: str = ""
    for _ in range(HEADER - len(length)):
        length_to_add += FILL_LENGTH_CHAR

    return length + length_to_add

# XOR encrypt/decrypt
def cypher(message: bytes, key: bytes) -> bytes:
    """Cypher encrypt/decrypt function for message with the given xor key.

    Args:
        message (str): Message to cypher
        key (bytes): XOR key to use

    Returns:
        bytes: Ciphered message
    """    
    cyphered: bytes = b''
    for i in range(len(message)):
        cyphered += bytes([message[i] ^ key[i % len(key)]])
    return cyphered

# Encrypt message with public key
def encrypt(message: bytes, public_key: bytes) -> bytes:
    """Encrypt a message with the public key (used to send securely the XOR key)

    Args:
        message (bytes): Message to encrypt (XOR key)
        public_key (RsaKey): Public key to encrypt the message 

    Returns:
        bytes: Encrypted message
    """    
    # Convert public key to RSA object
    pubKey: RsaKey = RSA.import_key(public_key)
    cipher = PKCS1_OAEP.new(pubKey)
    
    # Encrypt message with RSA
    ciphertext: bytes = cipher.encrypt(message)
    return ciphertext

# Decrypt message with private key
def decrypt(message: bytes, private_key: bytes):
    """Decrypt message with private key (used to decrypt the XOR key)

    Args:
        message (bytes): Message to decrypt
        private_key (bytes): Private key to use for decryption

    Returns:
        bytes: Decrypted message
    """    
    # Convert private key to RSA object
    privKey: RsaKey = RSA.import_key(private_key)
    cipher = PKCS1_OAEP.new(privKey)
    
    # Decrypt message with RSA
    plaintext: bytes = cipher.decrypt(message)
    return plaintext

# Socket client using RSA above
class Client:
    def __init__(self, host: str, port: int):
        """Initialize the client and connect to the server using the given host and port

        Args:
            host (str): IP address of the server
            port (int): Port where the server is listening on
        """        
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def generate_xor_key(self, size: int = 16):
        """Generate the XOR key used for message encription.

        Args:
            size (int, optional): Size of the XOR key. Defaults to 16.

        Returns:
            bytes: Generated XOR key
        """        
        return os.urandom(size)

    def exchange_keys(self, xor_key: bytes):
        """Sends the XOR key to the server using its public RSA key.

        Args:
            xor_key (bytes): XOR key to send
        """        
        serv_pub_key: bytes = self.sock.recv(2048)
        self.sock.send(encrypt(xor_key, serv_pub_key))
        
    def send(self, message: bytes, xor_key: bytes=None):
        """Sends a message to the server using the XOR key if provided.

        Args:
            message (bytes): Message to send
            xor_key (bytes, optional): XOR key to use for encryption. Defaults to None.
        """        
        if (xor_key):
            # Encrypt message with public key
            message = cypher(message, xor_key)
            message = message + b'encrypted'
        # Send message
        self.sock.send(str(fill_length(str(len(message)))).encode())
        self.sock.send(message)

    def receive(self, xor_key : bytes=None):
        """Recieve the message and decrypt it if necessary

        Args:
            xor_key (bytes, optional): XOR key to use if needed. Defaults to None.

        Returns:
            bytes: Received decrypted message
        """        
        # Receive message
        message_length: str = self.sock.recv(HEADER).decode()
        length: int = int(message_length.replace(FILL_LENGTH_CHAR, ""))
        message: bytes = self.sock.recv(length)
        if (message.endswith(b'encrypted') and xor_key):
            message = message[:-9]
            # Decrypt message with private key
            message = cypher(message, xor_key)
        return message

    # Function that will send a file
    def send_file(self, file_name: str, xor_key: bytes=None):
        """Sends the given file to the server using the XOR key if provided.

        Args:
            file_name (str): Name of the file to send
            xor_key (bytes, optional): XOR key to use if needed. Defaults to None.
        """        
        # Send file name
        self.send(file_name.encode(), xor_key)
        # Send file
        with open(file_name, 'rb') as f:
            file_data: bytes = f.read()
        self.send(file_data, xor_key)

    # Function that will receive a file
    def receive_file(self, xor_key: bytes=None, folder: str="download_client"):
        """Recieve a file from the server and decrypt it if needed with the XOR key.

        Args:
            xor_key (bytes, optional): XOR key to use if needed. Defaults to None.
            folder (str, optional): The folder where the file will be received. Defaults to "download_client".

        Returns:
            str: Name of the received file.
        """        
        # Receive file name
        file_name: str = self.receive(xor_key).decode()
        # Receive file
        file_data: bytes = self.receive(xor_key)
        # Check if download folder exists
        if not os.path.isdir(folder):
            os.mkdir(folder)
        # Save file
        with open(f"{folder}/{file_name}", 'wb') as f:
            f.write(file_data)
        return file_name
    
# Socket server using RSA above
class Server:
    def __init__(self, host: str, port: int):
        """Initialize the server with the given host and port.

        Args:
            host (str): IP address of the interface to listen on.
            port (int): Port to listen on.
        """        
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        
    def generate_keys(self, KEYSIZE: int =2048) -> Tuple[bytes, bytes]:
        """Generate RSA key pair for XOR key secure exchange

        Args:
            KEYSIZE (int, optional): Size of the keys. Defaults to 2048.

        Returns:
            Tuple[bytes, bytes]: public key and private key
        """    
        key: RsaKey = RSA.generate(KEYSIZE)
        public_key: RsaKey = key.publickey()
        private_key: RsaKey = key
        
        # Convert keys to bytes and return them
        pubKey: bytes = public_key.export_key()
        privKey: bytes = private_key.export_key()
        return pubKey, privKey

    def exchange_keys(self, conn: socket.socket, serv_pub_key: bytes, serv_priv_key: bytes) -> bytes:
        """Sends the public key of the server to the client, and receive the XOR key from it.

        Args:
            conn (socket.socket): Connection with the client
            serv_pub_key (bytes): Public key of the server
            serv_priv_key (bytes): Private key of the server

        Returns:
            bytes: XOR key
        """        
        # Send public key to client
        conn.send(serv_pub_key)
        # Receive xor key from client
        xor_key = conn.recv(1024)
        
        return decrypt(xor_key, serv_priv_key)
    
    def recv_client(self) -> socket.socket:
        """Accepts a client connection and returns it.

        Returns:
            socket.socket: Connection with the client (conventionally named 'conn')
        """        
        # Accept connection
        conn, addr = self.sock.accept()
        return conn
        
    def receive(self, conn: socket.socket, xor_key: bytes=None) -> bytes:
        """Recieve a message from the client and decrypt it if nedded with the provided XOR key.

        Args:
            conn (socket.socket): Connection with the client
            xor_key (bytes, optional): XOR key if needed. Defaults to None.

        Returns:
            bytes: Decrypted message from the client
        """        
        # Receive message
        self.message_length: str = conn.recv(HEADER).decode()
        self.length: int = int(self.message_length.replace(FILL_LENGTH_CHAR, ""))

        message: bytes = conn.recv(self.length)
        if (message.endswith(b'encrypted') and xor_key):
            message = message[:-9]
            # Decrypt message with private key
            message = cypher(message, xor_key)
        return message

    def send(self, conn: socket.socket, message: bytes, xor_key: bytes=None):
        """Sends a message to specified client and encrypt it with the given XOR key if provided.

        Args:
            conn (socket.socket): Connection with the client
            message (bytes): Message to send
            xor_key (bytes, optional): XOR key to use. Defaults to None.
        """
        # Encrypt message with public key
        if (xor_key):
            message = cypher(message, xor_key)
            message = message + b'encrypted'
        # Send message
        conn.send(str(fill_length(str(len(message)))).encode())
        conn.send(message)

    # Function that will send a file
    def send_file(self, conn: socket.socket, file_name: str, xor_key: bytes=None):
        """Sends a file to the client and encrypt it with the given XOR key if provided.

        Args:
            conn (socket.socket): Connection with the client
            file_name (str): Name of the file to send
            xor_key (bytes, optional): XOR key to use. Defaults to None.
        """        
        # Send file name
        self.send(conn, file_name.encode(), xor_key)
        # Open file
        with open(file_name, 'rb') as f:
            file_data = f.read()
        self.send(conn, file_data, xor_key)

    # Function that will receive a file
    def receive_file(self, conn: socket.socket, xor_key: bytes=None, folder: str="download_server"):
        """Recieve a file from the client, decrypt it if needed, and write it to the disk.

        Args:
            conn (socket.socket): Connection with the client
            xor_key (bytes, optional): XOR key to use. Defaults to None.
            folder (str, optional): The folder where the file will be received. Defaults to "download_server".

        Returns:
            str: Name of the received file
        """        
        file_name: str = self.receive(conn, xor_key).decode()
        file_data: bytes = self.receive(conn, xor_key)
        # Check if download folder exists
        if not os.path.isdir(folder):
            os.mkdir(folder)
        with open(f"{folder}/{file_name}", 'wb') as f:
            f.write(file_data)
        return file_name

if __name__ == '__main__':
    ERR_MSG = """
    This is a library, and not an executable python program.
    Please, use the library by importing it using one of the lines below:
    
        import libsocket
        from libsocket import Client
        from libsocket import Server
        from libsocket import *
    """
    print(ERR_MSG)