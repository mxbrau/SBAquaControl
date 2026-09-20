#ifndef __OTA_SERIAL_H_
#define __OTA_SERIAL_H_

#include <Arduino.h>

#if defined(ESP8266) && defined(USE_OTA_SERIAL)

#include <ESP8266WiFi.h>

#ifndef OTA_SERIAL_BUFFER_LEN
#define OTA_SERIAL_BUFFER_LEN 1024
#endif

class OtaSerialLogger : public Print
{
public:
	void begin();
	void handle();
	size_t write(uint8_t value) override;
	size_t write(const uint8_t *buffer, size_t size) override;
	void flush() override;

private:
	WiFiServer _server = WiFiServer(23);
	WiFiClient _client;
	bool _started = false;
	uint8_t _buffer[OTA_SERIAL_BUFFER_LEN];
	size_t _bufferStart = 0;
	size_t _bufferLen = 0;

	void storeBuffered(uint8_t value);
	void flushBufferedToClient();
};

extern OtaSerialLogger OtaSerial;

#endif

#endif // __OTA_SERIAL_H_
