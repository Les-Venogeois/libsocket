using LibSocket;

// Start client
var client = new Client("127.0.0.1", 4444);
Console.WriteLine("Client started");

var xorKey = client.GenerateXorKey();
Console.WriteLine("XOR key generated");

client.ExchangeKeys(xorKey);
Console.WriteLine("Keys exchanged");

client.SendFile("../test.txt", xorKey);
Console.WriteLine("File sent");

client.Dispose();
Console.WriteLine("Client closed");
