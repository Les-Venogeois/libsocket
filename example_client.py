from libsocket import Client

# Start client
client = Client('127.0.0.1', 4444)
print("Client started")
XOR_KEY = client.generate_xor_key()
print("XOR key generated")
client.exchange_keys(XOR_KEY)
print("Keys exchanged")
client.send_file("Diagramme.png", XOR_KEY)
print("File sent")
