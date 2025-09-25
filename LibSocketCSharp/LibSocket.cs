using System.Net;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;

namespace LibSocket;

/// <summary>
/// Socket client and server library with RSA+XOR encryption support.
/// Direct C# port of the Python libsocket library maintaining exact one-to-one functionality.
/// </summary>
public static class LibSocketConfig
{
    public const int HEADER = 64;
    public const string FILL_LENGTH_CHAR = "a";
}

/// <summary>
/// Utility functions for LibSocket
/// </summary>
public static class LibSocketUtils
{
    /// <summary>
    /// Fill the message containing the length of the message to fit in the header.
    /// </summary>
    /// <param name="length">Actual length of the message (digit)</param>
    /// <returns>Size of the message with the correct length</returns>
    public static string FillLength(string length)
    {
        var lengthToAdd = "";
        for (int i = 0; i < LibSocketConfig.HEADER - length.Length; i++)
        {
            lengthToAdd += LibSocketConfig.FILL_LENGTH_CHAR;
        }
        return length + lengthToAdd;
    }

    /// <summary>
    /// Cypher encrypt/decrypt function for message with the given xor key.
    /// </summary>
    /// <param name="message">Message to cypher</param>
    /// <param name="key">XOR key to use</param>
    /// <returns>Ciphered message</returns>
    public static byte[] Cypher(byte[] message, byte[] key)
    {
        var cyphered = new byte[message.Length];
        for (int i = 0; i < message.Length; i++)
        {
            cyphered[i] = (byte)(message[i] ^ key[i % key.Length]);
        }
        return cyphered;
    }

    /// <summary>
    /// Encrypt a message with the public key (used to send securely the XOR key)
    /// </summary>
    /// <param name="message">Message to encrypt (XOR key)</param>
    /// <param name="publicKeyBytes">Public key to encrypt the message</param>
    /// <returns>Encrypted message</returns>
    public static byte[] Encrypt(byte[] message, byte[] publicKeyBytes)
    {
        using var rsa = RSA.Create();
        rsa.ImportRSAPublicKey(publicKeyBytes, out _);
        return rsa.Encrypt(message, RSAEncryptionPadding.OaepSHA256);
    }

    /// <summary>
    /// Decrypt message with private key (used to decrypt the XOR key)
    /// </summary>
    /// <param name="message">Message to decrypt</param>
    /// <param name="privateKeyBytes">Private key to use for decryption</param>
    /// <returns>Decrypted message</returns>
    public static byte[] Decrypt(byte[] message, byte[] privateKeyBytes)
    {
        using var rsa = RSA.Create();
        rsa.ImportRSAPrivateKey(privateKeyBytes, out _);
        return rsa.Decrypt(message, RSAEncryptionPadding.OaepSHA256);
    }
}

/// <summary>
/// Socket client using RSA encryption for key exchange and XOR for message encryption
/// </summary>
public class Client : IDisposable
{
    private readonly string _host;
    private readonly int _port;
    private Socket? _socket;
    private bool _disposed;

    /// <summary>
    /// Initialize the client and connect to the server using the given host and port
    /// </summary>
    /// <param name="host">IP address of the server</param>
    /// <param name="port">Port where the server is listening on</param>
    public Client(string host, int port)
    {
        _host = host;
        _port = port;
        _socket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        _socket.Connect(IPAddress.Parse(_host), _port);
    }

    /// <summary>
    /// Generate the XOR key used for message encryption.
    /// </summary>
    /// <param name="size">Size of the XOR key. Defaults to 16.</param>
    /// <returns>Generated XOR key</returns>
    public byte[] GenerateXorKey(int size = 16)
    {
        return RandomNumberGenerator.GetBytes(size);
    }

    /// <summary>
    /// Sends the XOR key to the server using its public RSA key.
    /// </summary>
    /// <param name="xorKey">XOR key to send</param>
    public void ExchangeKeys(byte[] xorKey)
    {
        if (_socket == null) throw new ObjectDisposedException(nameof(Client));
        
        var servPubKeyBuffer = new byte[2048];
        int bytesReceived = _socket.Receive(servPubKeyBuffer);
        var servPubKey = new byte[bytesReceived];
        Array.Copy(servPubKeyBuffer, servPubKey, bytesReceived);
        
        var encryptedXorKey = LibSocketUtils.Encrypt(xorKey, servPubKey);
        _socket.Send(encryptedXorKey);
    }

    /// <summary>
    /// Sends a message to the server using the XOR key if provided.
    /// </summary>
    /// <param name="message">Message to send</param>
    /// <param name="xorKey">XOR key to use for encryption. Defaults to null.</param>
    public void Send(byte[] message, byte[]? xorKey = null)
    {
        if (_socket == null) throw new ObjectDisposedException(nameof(Client));

        if (xorKey != null)
        {
            // Encrypt message with XOR key
            message = LibSocketUtils.Cypher(message, xorKey);
            message = message.Concat(Encoding.UTF8.GetBytes("encrypted")).ToArray();
        }

        // Send message length header
        var lengthHeader = Encoding.UTF8.GetBytes(LibSocketUtils.FillLength(message.Length.ToString()));
        _socket.Send(lengthHeader);
        
        // Send message
        _socket.Send(message);
    }

    /// <summary>
    /// Receive the message and decrypt it if necessary
    /// </summary>
    /// <param name="xorKey">XOR key to use if needed. Defaults to null.</param>
    /// <returns>Received decrypted message</returns>
    public byte[] Receive(byte[]? xorKey = null)
    {
        if (_socket == null) throw new ObjectDisposedException(nameof(Client));

        // Receive message length header
        var headerBuffer = new byte[LibSocketConfig.HEADER];
        _socket.Receive(headerBuffer);
        var messageLengthStr = Encoding.UTF8.GetString(headerBuffer).Replace(LibSocketConfig.FILL_LENGTH_CHAR, "");
        var messageLength = int.Parse(messageLengthStr);

        // Receive message
        var messageBuffer = new byte[messageLength];
        int totalReceived = 0;
        while (totalReceived < messageLength)
        {
            int received = _socket.Receive(messageBuffer, totalReceived, messageLength - totalReceived, SocketFlags.None);
            totalReceived += received;
        }

        var message = messageBuffer;
        var encryptedSuffix = Encoding.UTF8.GetBytes("encrypted");
        
        if (message.Length >= encryptedSuffix.Length && 
            message.TakeLast(encryptedSuffix.Length).SequenceEqual(encryptedSuffix) && 
            xorKey != null)
        {
            // Remove "encrypted" suffix and decrypt
            message = message.Take(message.Length - encryptedSuffix.Length).ToArray();
            message = LibSocketUtils.Cypher(message, xorKey);
        }
        
        return message;
    }

    /// <summary>
    /// Sends the given file to the server using the XOR key if provided.
    /// </summary>
    /// <param name="fileName">Name of the file to send</param>
    /// <param name="xorKey">XOR key to use if needed. Defaults to null.</param>
    public void SendFile(string fileName, byte[]? xorKey = null)
    {
        // Send file name
        Send(Encoding.UTF8.GetBytes(fileName), xorKey);
        
        // Send file content
        var fileData = File.ReadAllBytes(fileName);
        Send(fileData, xorKey);
    }

    /// <summary>
    /// Receive a file from the server and decrypt it if needed with the XOR key.
    /// </summary>
    /// <param name="xorKey">XOR key to use if needed. Defaults to null.</param>
    /// <param name="folder">The folder where the file will be received. Defaults to "download_client".</param>
    /// <returns>Name of the received file.</returns>
    public string ReceiveFile(byte[]? xorKey = null, string folder = "download_client")
    {
        // Receive file name
        var fileNameBytes = Receive(xorKey);
        var fileName = Encoding.UTF8.GetString(fileNameBytes);
        
        // Receive file data
        var fileData = Receive(xorKey);
        
        // Check if download folder exists
        if (!Directory.Exists(folder))
        {
            Directory.CreateDirectory(folder);
        }
        
        // Save file
        var filePath = Path.Combine(folder, fileName);
        File.WriteAllBytes(filePath, fileData);
        
        return fileName;
    }

    public void Dispose()
    {
        if (!_disposed)
        {
            _socket?.Close();
            _socket?.Dispose();
            _socket = null;
            _disposed = true;
        }
    }
}

/// <summary>
/// Socket server using RSA encryption for key exchange and XOR for message encryption
/// </summary>
public class Server : IDisposable
{
    private readonly string _host;
    private readonly int _port;
    private Socket? _socket;
    private bool _disposed;

    /// <summary>
    /// Initialize the server with the given host and port.
    /// </summary>
    /// <param name="host">IP address of the interface to listen on.</param>
    /// <param name="port">Port to listen on.</param>
    public Server(string host, int port)
    {
        _host = host;
        _port = port;
        _socket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        _socket.Bind(new IPEndPoint(IPAddress.Parse(_host), _port));
        _socket.Listen(5);
    }

    /// <summary>
    /// Generate RSA key pair for XOR key secure exchange
    /// </summary>
    /// <param name="keySize">Size of the keys. Defaults to 2048.</param>
    /// <returns>Tuple of public key and private key</returns>
    public (byte[] PublicKey, byte[] PrivateKey) GenerateKeys(int keySize = 2048)
    {
        using var rsa = RSA.Create(keySize);
        var publicKey = rsa.ExportRSAPublicKey();
        var privateKey = rsa.ExportRSAPrivateKey();
        return (publicKey, privateKey);
    }

    /// <summary>
    /// Sends the public key of the server to the client, and receive the XOR key from it.
    /// </summary>
    /// <param name="conn">Connection with the client</param>
    /// <param name="servPubKey">Public key of the server</param>
    /// <param name="servPrivKey">Private key of the server</param>
    /// <returns>XOR key</returns>
    public byte[] ExchangeKeys(Socket conn, byte[] servPubKey, byte[] servPrivKey)
    {
        // Send public key to client
        conn.Send(servPubKey);
        
        // Receive encrypted XOR key from client
        var buffer = new byte[1024];
        int bytesReceived = conn.Receive(buffer);
        var encryptedXorKey = new byte[bytesReceived];
        Array.Copy(buffer, encryptedXorKey, bytesReceived);
        
        return LibSocketUtils.Decrypt(encryptedXorKey, servPrivKey);
    }

    /// <summary>
    /// Accepts a client connection and returns it.
    /// </summary>
    /// <returns>Connection with the client</returns>
    public Socket Accept()
    {
        if (_socket == null) throw new ObjectDisposedException(nameof(Server));
        return _socket.Accept();
    }

    /// <summary>
    /// Receive a message from the client and decrypt it if needed with the provided XOR key.
    /// </summary>
    /// <param name="conn">Connection with the client</param>
    /// <param name="xorKey">XOR key if needed. Defaults to null.</param>
    /// <returns>Decrypted message from the client</returns>
    public byte[] Receive(Socket conn, byte[]? xorKey = null)
    {
        // Receive message length header
        var headerBuffer = new byte[LibSocketConfig.HEADER];
        conn.Receive(headerBuffer);
        var messageLengthStr = Encoding.UTF8.GetString(headerBuffer).Replace(LibSocketConfig.FILL_LENGTH_CHAR, "");
        var messageLength = int.Parse(messageLengthStr);

        // Receive message
        var messageBuffer = new byte[messageLength];
        int totalReceived = 0;
        while (totalReceived < messageLength)
        {
            int received = conn.Receive(messageBuffer, totalReceived, messageLength - totalReceived, SocketFlags.None);
            totalReceived += received;
        }

        var message = messageBuffer;
        var encryptedSuffix = Encoding.UTF8.GetBytes("encrypted");
        
        if (message.Length >= encryptedSuffix.Length && 
            message.TakeLast(encryptedSuffix.Length).SequenceEqual(encryptedSuffix) && 
            xorKey != null)
        {
            // Remove "encrypted" suffix and decrypt
            message = message.Take(message.Length - encryptedSuffix.Length).ToArray();
            message = LibSocketUtils.Cypher(message, xorKey);
        }
        
        return message;
    }

    /// <summary>
    /// Sends a message to specified client and encrypt it with the given XOR key if provided.
    /// </summary>
    /// <param name="conn">Connection with the client</param>
    /// <param name="message">Message to send</param>
    /// <param name="xorKey">XOR key to use. Defaults to null.</param>
    public void Send(Socket conn, byte[] message, byte[]? xorKey = null)
    {
        if (xorKey != null)
        {
            // Encrypt message with XOR key
            message = LibSocketUtils.Cypher(message, xorKey);
            message = message.Concat(Encoding.UTF8.GetBytes("encrypted")).ToArray();
        }

        // Send message length header
        var lengthHeader = Encoding.UTF8.GetBytes(LibSocketUtils.FillLength(message.Length.ToString()));
        conn.Send(lengthHeader);
        
        // Send message
        conn.Send(message);
    }

    /// <summary>
    /// Sends a file to the client and encrypt it with the given XOR key if provided.
    /// </summary>
    /// <param name="conn">Connection with the client</param>
    /// <param name="fileName">Name of the file to send</param>
    /// <param name="xorKey">XOR key to use. Defaults to null.</param>
    public void SendFile(Socket conn, string fileName, byte[]? xorKey = null)
    {
        // Send file name
        Send(conn, Encoding.UTF8.GetBytes(fileName), xorKey);
        
        // Send file content
        var fileData = File.ReadAllBytes(fileName);
        Send(conn, fileData, xorKey);
    }

    /// <summary>
    /// Receive a file from the client, decrypt it if needed, and write it to the disk.
    /// </summary>
    /// <param name="conn">Connection with the client</param>
    /// <param name="xorKey">XOR key to use. Defaults to null.</param>
    /// <param name="folder">The folder where the file will be received. Defaults to "download_server".</param>
    /// <returns>Name of the received file</returns>
    public string ReceiveFile(Socket conn, byte[]? xorKey = null, string folder = "download_server")
    {
        // Receive file name
        var fileNameBytes = Receive(conn, xorKey);
        var fileName = Encoding.UTF8.GetString(fileNameBytes);
        
        // Receive file data
        var fileData = Receive(conn, xorKey);
        
        // Check if download folder exists
        if (!Directory.Exists(folder))
        {
            Directory.CreateDirectory(folder);
        }
        
        // Save file
        var filePath = Path.Combine(folder, fileName);
        File.WriteAllBytes(filePath, fileData);
        
        return fileName;
    }

    public void Dispose()
    {
        if (!_disposed)
        {
            _socket?.Close();
            _socket?.Dispose();
            _socket = null;
            _disposed = true;
        }
    }
}