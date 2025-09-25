using LibSocket;

const int KEYSIZE = 1024;

// Start server with private key
var server = new Server("127.0.0.1", 4444);
var (publicKey, privateKey) = server.GenerateKeys(KEYSIZE);
Console.WriteLine("Keys generated");

var conn = server.Accept();
Console.WriteLine("Client connected");

var xorKey = server.ExchangeKeys(conn, publicKey, privateKey);
Console.WriteLine("Keys exchanged");

// Delete private key and public key from memory - disabled for multiple client support
// privateKey = null;
// publicKey = null;
// Console.WriteLine("Keys deleted");

var filename = server.ReceiveFile(conn, xorKey);
Console.WriteLine($"File \"{filename}\" received");

server.Dispose();
Console.WriteLine("Server closed");
