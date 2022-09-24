# Libsocket
## Principle
The idea behind this library is to facilitate the communication between python clients and servers. It will automatically make the connection, and has the ability to send and receive messages and files. The connection can optionally be encrypted using XOR cypher. The XOR key is exchanged securely with an RSA keypair provided by the server. The encryption protocol is inspired by the SSH protocol, and described below.

## Encryption
### Client
The client will send a special request to the server to ask for its public key for asymmetric encryption. The client will wait for the response from the server, and store the key sent in response by the server.

The client will then generate a random symmetric encryption key (a XOR key seems simple and efficient to me). It will encrypt the generated symmetric key with the previously received server's public key, and send the encrypted key to the server.

The server will then store the symmetric encryption key, and use it to decrypt and encrypt the messages during the communication process.

The client will have the ability to encrypt and decrypt the messages using the XOR key previously generated. The client can choose if it wants to encrypt the messages, however, once the key has been sent to the server, all the messages sent by the server to the client will be encrypted.

### Serveur
The server will wait for a connection request. When a client will ask him for his previously generated public key, he will send it to the client, and wait for the sending of the symmetric key.

When it receives the symmetric key, it will save it and use it to encrypt all messages sent to the client. If a recived message is encrypted, it will be decrypted with this same key.

### Diagramm (in french)
![Diagramm of the key exchage algorythm (in french)](Diagramme.png)

## Dependencies
In order to be able to use the library correctly, you will need to install the `pycryptodome` module (which is used for encryped communication). You can install it using one of two commands after cloning the repository:

`pip3 install pycryptodome`

`pip3 install -r requirements.txt`
