from libsocket import *
KEYSIZE = 1024
public_key, private_key = generate_keys(KEYSIZE)
print("Keys generated")

# Start server with private key
server = Server('127.0.0.1', 4444)
conn = server.recv_client()
print("Client connected")
xor_key = server.exchange_keys(conn, public_key, private_key)
print("Keys exchanged")

# Delete private key and public key from memory
# Disabled beacause planning adding multiple client support
# del private_key
# del public_key
# print("Keys deleted")

filename = server.receive_file(conn, xor_key)
print(f'File "{filename}" received')