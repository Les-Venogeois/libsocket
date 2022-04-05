from libsocket import *
from os import urandom
    
# Generate xor key
xor_key = urandom(16)

# Start client
client = Client('127.0.0.1', 4444)
print("Client started")
client.exchange_keys(xor_key)
client.send_file("Diagramme.png", xor_key)
