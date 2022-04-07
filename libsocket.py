# Make a socket client/server encrypted with RSA
import os
import socket
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

HEADER = 64
FILL_LENGTH_CHAR = "a"

def fill_length(length):
    # length is a str argument that is the actual length of the message (digit)
    length_to_add = ""
    for __ in range(HEADER - len(length)):
        length_to_add += FILL_LENGTH_CHAR

    return length + length_to_add # type = str

# XOR encrypt/decrypt
def cypher(message, key):
    cyphered = b''
    for i in range(len(message)):
        cyphered += bytes([message[i] ^ key[i % len(key)]])
    return cyphered

def generate_keys(KEYSIZE=2048):
    key = RSA.generate(KEYSIZE)
    public_key = key.publickey()
    private_key = key
    
    # Convert keys to bytes and return them
    public_key = public_key.export_key()
    private_key = private_key.export_key()
    return public_key, private_key

# Encrypt message with public key
def encrypt(message, public_key):
    # Convert public key to RSA object
    public_key = RSA.import_key(public_key)
    cipher = PKCS1_OAEP.new(public_key)
    
    # Encrypt message with RSA
    ciphertext = cipher.encrypt(message)
    return ciphertext

# Decrypt message with private key
def decrypt(message, private_key):    
    # Convert private key to RSA object
    private_key = RSA.import_key(private_key)
    cipher = PKCS1_OAEP.new(private_key)
    
    # Decrypt message with RSA
    plaintext = cipher.decrypt(message)
    return plaintext

# Socket client using RSA above
class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def exchange_keys(self, xor_key):
        serv_pub_key = self.sock.recv(2048)
        self.sock.send(encrypt(xor_key, serv_pub_key))
        
    def send(self, message, xor_key=None):
        if (xor_key != None):
            # Encrypt message with public key
            message = cypher(message, xor_key)
            message = message + b'encrypted'
        # Send message
        self.sock.send(str(fill_length(str(len(message)))).encode())
        self.sock.send(message)

    def receive(self, xor_key=None):
        # Receive message
        message_length = self.sock.recv(HEADER).decode()
        message_length = int(message_length.replace(FILL_LENGTH_CHAR, ""))
        message = self.sock.recv(message_length)
        if message.endswith(b'encrypted'):
            message = message[:-9]
            # Decrypt message with private key
            message = cypher(message, xor_key)
        return message

    # Function that will send a file
    def send_file(self, file_name, xor_key=None):
        # Send file name
        self.send(file_name.encode(), xor_key)
        # Send file
        with open(file_name, 'rb') as f:
            file_data = f.read()
        self.send(file_data, xor_key)

    # Function that will receive a file
    def receive_file(self, xor_key=None):
        # Receive file name
        file_name = self.receive(xor_key).decode()
        # Receive file
        file_data = self.receive(xor_key)
        # Check if download folder exists
        if not os.path.isdir('download_client'):
            os.mkdir('download_client')
        # Save file
        with open(f"download_client/{file_name}", 'wb') as f:
            f.write(file_data)
        return file_name
    
# Socket server using RSA above
class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        
    def exchange_keys(self, conn, serv_pub_key, serv_priv_key):
        # Send public key to client
        conn.send(serv_pub_key)
        # Receive xor key from client
        xor_key = conn.recv(1024)
        
        return decrypt(xor_key, serv_priv_key)
    
    def recv_client(self):
        # Accept connection
        conn, addr = self.sock.accept()
        return conn
        
    def receive(self, conn, xor_key=None):
        # Receive message
        self.message_length = conn.recv(HEADER).decode()
        self.message_length = int(self.message_length.replace(FILL_LENGTH_CHAR, ""))

        message = conn.recv(self.message_length)
        if message.endswith(b'encrypted'):
            message = message[:-9]
            # Decrypt message with private key
            message = cypher(message, xor_key)
        return message

    def send(self, conn, message, xor_key=None):
        # Encrypt message with public key
        if xor_key != None:
            message = cypher(message, xor_key)
            message = message + b'encrypted'
        # Send message
        conn.send(str(fill_length(str(len(message)))).encode())
        conn.send(message)

    # Function that will send a file
    def send_file(self, conn, file_name, xor_key=None):
        # Send file name
        self.send(conn, file_name.encode(), xor_key)
        # Open file
        with open(file_name, 'rb') as f:
            file_data = f.read()
        self.send(conn, file_data, xor_key)

    # Function that will receive a file
    def receive_file(self, conn, xor_key=None):
        file_name = self.receive(conn, xor_key).decode()
        file_data = self.receive(conn, xor_key)
        # Check if download folder exists
        if not os.path.isdir('download_server'):
            os.mkdir('download_server')
        with open(f"download_server/{file_name}", 'wb') as f:
            f.write(file_data)
        return file_name
