#include <SPI.h>
#include <LoRa.h>
#define SS //BOTAR PINO AQUI
#define RESET //BOTAR PINO AQUI
#define DIO0 //BOTAR PINO AQUI
void setup()
{
Serial.begin(115200);
LoRa.setPins(SS, RESET, DIO0);
Serial.println("Verificando LoRa Receptor");
// Inicializa o LoRa na frequência 915 MHz
if (!LoRa.begin(915E6))
{
Serial.println("Falha ao iniciar LoRa Receptor!");
while (1);// Se falhar, entra em um loop infinito, basta verificar as
//ligações e reiniciar
}
Serial.println("LoRa Receptor inicializado com sucesso");
  }
void loop()
{
// Recebe o pacote
int packetSize = LoRa.parsePacket();
// Verifica se tem algo no pacote
if (packetSize)
{
Serial.print("Recebido: ");
// Lê o pacote
while (LoRa.available())
{
Serial.print((char)LoRa.read());
}
// Exibe o RSSI (força do sinal)
Serial.print(" | sinal RSSI: ");
Serial.println(LoRa.packetRssi());
}
}