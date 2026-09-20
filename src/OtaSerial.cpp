#include "OtaSerial.h"

#if defined(ESP8266) && defined(USE_OTA_SERIAL)

OtaSerialLogger OtaSerial;

void OtaSerialLogger::begin()
{
	if (_started)
	{
		return;
	}
	_server.begin();
	_server.setNoDelay(true);
	_started = true;
}

void OtaSerialLogger::handle()
{
	if (!_started)
	{
		return;
	}
	if (_client && !_client.connected())
	{
		_client.stop();
	}
	if (!_client || !_client.connected())
	{
		WiFiClient nextClient = _server.available();
		if (nextClient)
		{
			_client = nextClient;
			_client.setNoDelay(true);
			flushBufferedToClient();
		}
	}
}

size_t OtaSerialLogger::write(uint8_t value)
{
	::Serial.write(value);
	if (_client && _client.connected())
	{
		_client.write(value);
	}
	else
	{
		storeBuffered(value);
	}
	return 1;
}

size_t OtaSerialLogger::write(const uint8_t *buffer, size_t size)
{
	if (!buffer || size == 0)
	{
		return 0;
	}
	::Serial.write(buffer, size);
	if (_client && _client.connected())
	{
		_client.write(buffer, size);
	}
	else
	{
		for (size_t i = 0; i < size; ++i)
		{
			storeBuffered(buffer[i]);
		}
	}
	return size;
}

void OtaSerialLogger::flush()
{
	::Serial.flush();
	if (_client && _client.connected())
	{
		_client.flush();
	}
}

void OtaSerialLogger::storeBuffered(uint8_t value)
{
	const size_t insertPos = (_bufferStart + _bufferLen) % OTA_SERIAL_BUFFER_LEN;
	_buffer[insertPos] = value;
	if (_bufferLen < OTA_SERIAL_BUFFER_LEN)
	{
		_bufferLen++;
	}
	else
	{
		_bufferStart = (_bufferStart + 1) % OTA_SERIAL_BUFFER_LEN;
	}
}

void OtaSerialLogger::flushBufferedToClient()
{
	if (!(_client && _client.connected()) || _bufferLen == 0)
	{
		return;
	}
	for (size_t i = 0; i < _bufferLen; ++i)
	{
		const size_t idx = (_bufferStart + i) % OTA_SERIAL_BUFFER_LEN;
		_client.write(_buffer[idx]);
	}
	_client.flush();
	_bufferStart = 0;
	_bufferLen = 0;
}

#endif
