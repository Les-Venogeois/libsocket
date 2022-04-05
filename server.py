from libsocket import *
generate_keys()

# Load private key from file
with open('private_key.pem', 'rb') as f:
    private_key = f.read()
with open('public_key.pem', 'rb') as f:
    public_key = f.read()

# Start server with private key
server = Server('127.0.0.1', 4444)
conn = server.recv_client()
xor_key = server.exchange_keys(public_key, conn)
msg = server.receive(conn, xor_key)
print(msg)
server.send(conn, b'Hello!', xor_key)
input("Press enter to close...")