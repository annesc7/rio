#include <SPI.h>
#include <LoRa.h>
#define SS 5
#define RESET 4
#define DIO0 2
int counter = 0;
void setup()
{
Serial.begin(115200);
LoRa.setPins(SS, RESET, DIO0);
Serial.println("Verificando LoRa Transmissor");
// Inicializa o LoRa na frequência 915 MHz
if (!LoRa.begin(915E6))
{
Serial.println("Falha ao iniciar LoRa Transmissor!");
while (1);// Se falhar, entra em um loop infinito, basta verificar as
ligações e reiniciar
}
Serial.println("LoRa Transmissor inicializado com sucesso");
}
void loop()
{
Serial.print("Enviando pacote: ");
Serial.println(counter);
// Inicia o pacote LoRa e envia dados
LoRa.beginPacket();
LoRa.print("Voa Pisces!");
LoRa.print(counter); // Adiciona o contador ao pacote
LoRa.endPacket(); // Finaliza o pacote e envia
counter++;
// Aguarda 2 segundos antes de enviar o próximo pacote
delay(2000);
}
