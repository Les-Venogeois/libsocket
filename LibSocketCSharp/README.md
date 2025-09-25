# LibSocket C# Port

A cross-platform C# port of the Python libsocket library that facilitates secure communication between clients and servers with RSA+XOR encryption.

## Overview

This library provides exact one-to-one functionality with the Python `libsocket` library, maintaining the same:
- API signatures and method names (converted to C# naming conventions)
- RSA key exchange protocol
- XOR encryption for message and file transfer
- Message framing and protocol behavior

## Features

- **Client-Server Communication**: Easy-to-use socket client and server classes
- **RSA Key Exchange**: Secure exchange of XOR keys using RSA encryption
- **XOR Encryption**: Fast symmetric encryption for all messages and files
- **File Transfer**: Send and receive files with optional encryption  
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Multi-Framework**: Supports .NET 6.0, 8.0, and 9.0

## Installation

### NuGet Package (when published)
```bash
dotnet add package LibSocket.CSharp
```

### From Source
1. Clone this repository
2. Build the library: `cd LibSocketCSharp && dotnet build`
3. Reference the project in your application

## Usage

### Server Example

```csharp
using LibSocket;

const int KEYSIZE = 1024;

// Start server
var server = new Server("127.0.0.1", 4444);
var (publicKey, privateKey) = server.GenerateKeys(KEYSIZE);
Console.WriteLine("Keys generated");

var conn = server.Accept();
Console.WriteLine("Client connected");

var xorKey = server.ExchangeKeys(conn, publicKey, privateKey);
Console.WriteLine("Keys exchanged");

// Receive a file
var filename = server.ReceiveFile(conn, xorKey);
Console.WriteLine($"File \"{filename}\" received");

server.Dispose();
```

### Client Example

```csharp
using LibSocket;

// Connect to server
var client = new Client("127.0.0.1", 4444);
Console.WriteLine("Client started");

// Generate XOR key and exchange with server
var xorKey = client.GenerateXorKey();
Console.WriteLine("XOR key generated");

client.ExchangeKeys(xorKey);
Console.WriteLine("Keys exchanged");

// Send a file
client.SendFile("test.txt", xorKey);
Console.WriteLine("File sent");

client.Dispose();
```

## API Reference

### Client Class

#### Constructor
- `Client(string host, int port)` - Connect to server

#### Methods
- `byte[] GenerateXorKey(int size = 16)` - Generate XOR encryption key
- `void ExchangeKeys(byte[] xorKey)` - Exchange keys with server using RSA
- `void Send(byte[] message, byte[]? xorKey = null)` - Send message
- `byte[] Receive(byte[]? xorKey = null)` - Receive message
- `void SendFile(string fileName, byte[]? xorKey = null)` - Send file
- `string ReceiveFile(byte[]? xorKey = null, string folder = "download_client")` - Receive file

### Server Class

#### Constructor  
- `Server(string host, int port)` - Create server and bind to port

#### Methods
- `(byte[] PublicKey, byte[] PrivateKey) GenerateKeys(int keySize = 2048)` - Generate RSA key pair
- `byte[] ExchangeKeys(Socket conn, byte[] servPubKey, byte[] servPrivKey)` - Exchange keys with client
- `Socket Accept()` - Accept client connection
- `void Send(Socket conn, byte[] message, byte[]? xorKey = null)` - Send message to client
- `byte[] Receive(Socket conn, byte[]? xorKey = null)` - Receive message from client
- `void SendFile(Socket conn, string fileName, byte[]? xorKey = null)` - Send file to client
- `string ReceiveFile(Socket conn, byte[]? xorKey = null, string folder = "download_server")` - Receive file from client

## Protocol Details

The library implements the same encryption protocol as the Python version:

1. **Key Exchange**: Client requests server's public RSA key
2. **XOR Key Generation**: Client generates random XOR key
3. **Secure Transfer**: Client encrypts XOR key with server's public key and sends it
4. **Symmetric Encryption**: All subsequent messages use XOR encryption with the shared key

## Compatibility

- **Operating Systems**: Windows, Linux, macOS
- **Frameworks**: .NET 6.0, 8.0, 9.0  
- **Interoperability**: Full compatibility with Python libsocket clients/servers
- **Protocol**: Identical message framing and encryption as Python version

## License

GPL-3.0-or-later - Same as the original Python library

## Comparison with Python Version

| Feature | Python | C# |
|---------|---------|-----|
| Client class | ✅ | ✅ |
| Server class | ✅ | ✅ |
| RSA key generation | ✅ | ✅ |
| XOR encryption | ✅ | ✅ |
| File transfer | ✅ | ✅ |
| Message framing | ✅ | ✅ |
| Cross-platform | ✅ | ✅ |
| Method signatures | Python style | C# style (same functionality) |

The C# version maintains exact functional parity with the Python library while following C# naming conventions and best practices.