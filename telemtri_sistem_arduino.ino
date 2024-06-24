int paketNumarasi = 0;
int ledpin =13;

void setup() {
  Serial.begin(9600);
  pinMode(ledpin,OUTPUT);
  randomSeed(analogRead(0));
}

void loop() {

  if (Serial.available() > 0) {
    char receivedChar = Serial.read();  // Read the incoming data

    if (receivedChar == '1') {
      digitalWrite(ledpin, HIGH);}
    else if (receivedChar == '0') {
      digitalWrite(ledpin, LOW);}
      
      }  // Turn on the LED

  paketNumarasi += 1; // Increment paketNumarasi

  int uyduStatusu = random(0, 6);

  // Generating a 5-digit binary string for HATA KODU
  String hataKodu = "";
  for (int i = 0; i < 5; i++) {
    hataKodu += String(random(0, 2));
  }

  // Getting current time for GÖNDERME SAATİ
  String gondermeSaati = "01/01/2024,12:00:00";


  float yukseklik1 = random(0, 100) + random(0, 100) / 100.0;
  float yukseklik2 = random(0, 100) + random(0, 100) / 100.0;
  float irtifaFarki = abs(yukseklik1 - yukseklik2);

  float basinc1 = random(10, 50) + random(0, 100) / 100.0;
  float basinc2 = random(10, 50) + random(0, 100) / 100.0;

  float inisHizi = random(4, 18) + random(0, 100) / 100.0;
  float sicaklik = random(16, 40) + random(0, 100) / 100.0;
  float pilGerilimi = 11.2;

  float gps1Latitude = random(-90, 90) + random(0, 100) / 100.0;
  float gps1Longitude = random(-180, 180) + random(0, 10000) / 10000.0;
  float gps1Altitude = random(0, 100) + random(0, 100) / 100.0;

  float pitch = 0 + random(-100,100)/100.0;
  float roll = 0 + random(-100,100)/100.0;
  float yaw = 0 + random(-100,100)/100.0;

  // Generating a 4-character code for RHRH (Digit Letter Digit Letter)
  char rhrh[5];
  rhrh[0] = '0' + random(0, 10);
  rhrh[1] = 'A' + random(0, 26);
  rhrh[2] = '0' + random(0, 10);
  rhrh[3] = 'A' + random(0, 26);
  rhrh[4] = '\0';

  int iotData = random(0, 1024);
  int takimNo = 1881;  // Your specific team number

  Serial.print(paketNumarasi); Serial.print(",");
  Serial.print(uyduStatusu); Serial.print(",");
  Serial.print(hataKodu); Serial.print(",");
  Serial.print(gondermeSaati); Serial.print(",");
  Serial.print(basinc1); Serial.print(",");
  Serial.print(basinc2); Serial.print(",");
  Serial.print(yukseklik1); Serial.print(",");
  Serial.print(yukseklik2); Serial.print(",");
  Serial.print(irtifaFarki); Serial.print(",");
  Serial.print(inisHizi); Serial.print(",");
  Serial.print(sicaklik); Serial.print(",");
  Serial.print(pilGerilimi); Serial.print(",");
  Serial.print(gps1Latitude); Serial.print(",");
  Serial.print(gps1Longitude); Serial.print(",");
  Serial.print(gps1Altitude); Serial.print(",");
  Serial.print(pitch); Serial.print(",");
  Serial.print(roll); Serial.print(",");
  Serial.print(yaw); Serial.print(",");
  Serial.print(rhrh); Serial.print(",");
  Serial.print(iotData); Serial.print(",");
  Serial.println(takimNo);

  delay(1000);
}
