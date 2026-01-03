/*
Aqua Control Library

Creationdate: 2017-12-09
Created by Marcel Schulz (Schullebernd)

Further information on www.schullebernd.de

Copyright 2017
*/

#include "AquaControl.h"

#if defined(USE_WEBSERVER)

extern "C" ESP8266WebServer _Server;
extern "C" AquaControl *_aqc;
#if defined(USE_RTC_DS3231)
extern DS3232RTC RTC;
extern time_t getRTCTime();
#endif

void handleRoot()
{
	// Serve the new SPA UI (app.htm)
	File myFile = SD.open(F("app.htm"));
	if (!myFile)
	{
		_Server.send(404, "text/plain", "app.htm not found on SD card");
		Serial.println(F("error opening app.htm"));
		return;
	}

	_Server.setContentLength(CONTENT_LENGTH_UNKNOWN);
	_Server.send(200, "text/html", "");
	while (myFile.available())
	{
		String sLine = myFile.readStringUntil(10);
		sLine.replace("##FW_VERSION##", AQC_BUILD);
#if defined(USE_DS18B20_TEMP_SENSOR)
		char tempBuf[60];
		dtostrf(_aqc->_Temperature._TemperatureInCelsius, 1, 1, tempBuf);
		char fullTemp[100];
		sprintf(fullTemp, "Aktuelle Wassertemperatur %s &deg;C<br/>", tempBuf);
		sLine.replace("##TEMP##", fullTemp);
#else
		sLine.replace("##TEMP##", "");
#endif
		_Server.sendContent(sLine);
	}

	// close the file:
	myFile.close();
}

void handleNotFound()
{
	// Try to serve a static file from SD based on the requested URI
	String uri = _Server.uri();
	String path = uri;
	// Strip query string if present
	int qPos = path.indexOf('?');
	if (qPos != -1)
	{
		path = path.substring(0, qPos);
	}
	// Remove leading '/'
	if (path.startsWith("/"))
	{
		path = path.substring(1);
	}

	if (path.length() > 0)
	{
		File f = SD.open(path, FILE_READ);
		if (f)
		{
			// Minimal content-type detection
			String ct = "application/octet-stream";
			if (uri.endsWith(".htm") || uri.endsWith(".html"))
				ct = "text/html";
			else if (uri.endsWith(".css"))
				ct = "text/css";
			else if (uri.endsWith(".js"))
				ct = "application/javascript";
			else if (uri.endsWith(".json"))
				ct = "application/json";
			else if (uri.endsWith(".png"))
				ct = "image/png";
			else if (uri.endsWith(".jpg") || uri.endsWith(".jpeg"))
				ct = "image/jpeg";
			else if (uri.endsWith(".gif"))
				ct = "image/gif";

			_Server.streamFile(f, ct);
			f.close();
			return;
		}
	}

	// Fallback: diagnostic 404
	String message = "File Not Found\n\n";
	message += "URI: ";
	message += _Server.uri();
	message += "\nMethod: ";
	message += (_Server.method() == HTTP_GET) ? "GET" : "POST";
	message += "\nArguments: ";
	message += _Server.args();
	message += "\n";
	for (uint8_t i = 0; i < _Server.args(); i++)
	{
		message += " " + _Server.argName(i) + ": " + _Server.arg(i) + "\n";
	}
	_Server.send(404, "text/plain", message);
}

// === JSON API Endpoints ===

// Helper: Parse time string "HH:MM" or "MM:SS" or seconds to seconds
long parseTimeToSeconds(String timeStr)
{
	if (timeStr.indexOf(':') != -1)
	{
		int8_t index = timeStr.indexOf(':');
		int8_t first = timeStr.substring(0, index).toInt();
		int8_t second = timeStr.substring(index + 1).toInt();
		// Assume HH:MM for values >= 24, otherwise MM:SS
		if (first >= 24)
		{
			return (first * 60) + second; // MM:SS
		}
		else
		{
			return (first * 3600) + (second * 60); // HH:MM
		}
	}
	else
	{
		return timeStr.toInt();
	}
}

// API: GET /api/status
void handleApiStatus()
{
	// Stream JSON using char buffers - NO String objects to avoid heap crashes
	_Server.setContentLength(CONTENT_LENGTH_UNKNOWN);
	_Server.send(200, "application/json", "");

	char buf[16];

	_Server.sendContent("{\"test_mode\":");
	_Server.sendContent(_aqc->_PwmChannels[0].TestMode ? "true" : "false");

	// Current time (HH:MM:SS format)
	// NOTE: RTC stores local time (not UTC). Ensure RTC is set to your timezone.
	_Server.sendContent(",\"time\":\"");
	sprintf(buf, "%02d:%02d:%02d", hour(), minute(), second());
	_Server.sendContent(buf);

	_Server.sendContent("\",\"current_seconds\":");
	sprintf(buf, "%lu", (unsigned long)_aqc->CurrentSecOfDay);
	_Server.sendContent(buf);

	// Add time sync status fields
	_Server.sendContent(",\"time_source\":\"");
	const char *source = "unknown";
	if (_aqc->_LastTimeSyncSource == TimeSyncSource::Ntp)
		source = "ntp";
	else if (_aqc->_LastTimeSyncSource == TimeSyncSource::Rtc)
		source = "rtc";
	else if (_aqc->_LastTimeSyncSource == TimeSyncSource::Api)
		source = "api";
	_Server.sendContent(source);
	_Server.sendContent("\"");

#if defined(USE_RTC_DS3231)
	_Server.sendContent(",\"rtc_present\":true");
#else
	_Server.sendContent(",\"rtc_present\":false");
#endif

	// Time is valid if we have a sync source other than Unknown
	bool timeValid = (_aqc->_LastTimeSyncSource != TimeSyncSource::Unknown);
	bool needsSync = false;
#if defined(USE_NTP)
	needsSync = _aqc->_NtpSyncFailed;
#endif
	_Server.sendContent(",\"time_valid\":");
	_Server.sendContent(timeValid ? "true" : "false");
	_Server.sendContent(",\"needs_time_sync\":");
	_Server.sendContent(needsSync ? "true" : "false");

	// Last sync timestamp (for diagnostics)
	_Server.sendContent(",\"last_sync_ts\":");
	sprintf(buf, "%lu", (unsigned long)_aqc->_LastTimeSync);
	_Server.sendContent(buf);

#if defined(USE_DS18B20_TEMP_SENSOR)
	_Server.sendContent(",\"temperature\":");
	dtostrf(_aqc->_Temperature._TemperatureInCelsius, 1, 1, buf);
	_Server.sendContent(buf);
#else
	_Server.sendContent(",\"temperature\":0.0");
#endif

	_Server.sendContent(",\"wifi_connected\":true,\"sd_card_ok\":true,\"uptime\":");
	sprintf(buf, "%lu", millis() / 1000);
	_Server.sendContent(buf);

	// Add macro state to status response
#if defined(USE_WEBSERVER)
	if (_aqc->isMacroActive())
	{
		uint32_t remaining = _aqc->getMacroTimeRemaining();
		_Server.sendContent(",\"macro_active\":true,\"macro_expires_in\":");
		sprintf(buf, "%lu", (unsigned long)remaining);
		_Server.sendContent(buf);
		_Server.sendContent(",\"macro_id\":\"");
		_Server.sendContent(_aqc->_activeMacro.macroId);
		_Server.sendContent("\"");
	}
	else
	{
		_Server.sendContent(",\"macro_active\":false");
	}
#else
	_Server.sendContent(",\"macro_active\":false");
#endif

	_Server.sendContent("}");
}

// API: GET /api/schedule/get?channel=N
void handleApiScheduleGet()
{
	// Read channel from query and validate
	String channelStr = _Server.arg("channel");
	uint8_t channel = channelStr.toInt();
	if (channel >= 6)
	{
		_Server.send(400, "application/json", "{\"error\":\"Invalid channel (must be 0-5)\"}");
		return;
	}

	// Stream JSON to avoid large String allocations on ESP8266
	_Server.setContentLength(CONTENT_LENGTH_UNKNOWN);
	_Server.send(200, "application/json", "");

	char buf[48];
	sprintf(buf, "{\"channel\":%u,\"targets\":[", channel);
	_Server.sendContent(buf);

	for (uint8_t i = 0; i < _aqc->_PwmChannels[channel].TargetCount; i++)
	{
		if (i > 0)
			_Server.sendContent(",");
		sprintf(buf, "{\"time\":%lu,\"value\":%u,\"isControl\":true}",
				(unsigned long)_aqc->_PwmChannels[channel].Targets[i].Time,
				(unsigned int)_aqc->_PwmChannels[channel].Targets[i].Value);
		_Server.sendContent(buf);
	}
	_Server.sendContent("]}");
}

// API: GET /api/schedule/all
void handleApiScheduleAll()
{
	// Stream schedules to reduce RAM usage and avoid fragmentation
	_Server.setContentLength(CONTENT_LENGTH_UNKNOWN);
	_Server.send(200, "application/json", "");

	_Server.sendContent("{\"schedules\":[");

	char buf[48];
	for (uint8_t ch = 0; ch < 6; ch++)
	{
		if (ch > 0)
			_Server.sendContent(",");
		sprintf(buf, "{\"channel\":%u,\"targets\":[", ch);
		_Server.sendContent(buf);

		for (uint8_t i = 0; i < _aqc->_PwmChannels[ch].TargetCount; i++)
		{
			if (i > 0)
				_Server.sendContent(",");
			sprintf(buf, "{\"time\":%lu,\"value\":%u,\"isControl\":true}",
					(unsigned long)_aqc->_PwmChannels[ch].Targets[i].Time,
					(unsigned int)_aqc->_PwmChannels[ch].Targets[i].Value);
			_Server.sendContent(buf);
		}

		_Server.sendContent("]}");
	}
	_Server.sendContent("]}");
}

// API: POST /api/schedule/save
void handleApiScheduleSave()
{
	// Read JSON body (fallback to query args if body missing)
	String body = _Server.arg("plain");
	Serial.print(F("Schedule save body: "));
	Serial.println(body);

	// If body is empty, try minimal fallback parameters
	if (body.length() == 0 && _Server.hasArg("channel"))
	{
		// Build a tiny synthetic JSON for the minimal parser path
		String ch = _Server.arg("channel");
		String targets = _Server.arg("targets"); // optional, expected like [{"time":3600,"value":50},...]
		body.reserve(128);						 // Pre-allocate to avoid fragmentation
		body = "{\"channel\":";
		body += ch;
		body += ",\"targets\":";
		body += (targets.length() ? targets : "[]");
		body += "}";
	}

	// Parse channel
	int channelIdx = body.indexOf("\"channel\":");
	if (channelIdx == -1)
	{
		_Server.send(400, "application/json", "{\"error\":\"Missing channel\"}");
		return;
	}
	int channelStart = channelIdx + 10;
	int channelEnd = body.indexOf(',', channelStart);
	if (channelEnd == -1)
		channelEnd = body.indexOf('}', channelStart);
	String channelStr = body.substring(channelStart, channelEnd);
	channelStr.trim();
	uint8_t channel = channelStr.toInt();

	if (channel >= 6)
	{
		_Server.send(400, "application/json", "{\"error\":\"Invalid channel\"}");
		return;
	}

	// Clear existing targets
	for (uint8_t t = 0; t < MAX_TARGET_COUNT_PER_CHANNEL; t++)
	{
		_aqc->_PwmChannels[channel].removeTargetAt(0);
	}

	// Parse targets array
	int targetsIdx = body.indexOf("\"targets\":[");
	if (targetsIdx != -1)
	{
		int arrayStart = targetsIdx + 11;
		int arrayEnd = body.indexOf(']', arrayStart);
		String targetsStr = body.substring(arrayStart, arrayEnd);

		// Simple parser: split by },{
		unsigned int pos = 0;
		while (pos < targetsStr.length())
		{
			int objStart = targetsStr.indexOf('{', pos);
			if (objStart == -1)
				break;
			int objEnd = targetsStr.indexOf('}', objStart);
			if (objEnd == -1)
				break;

			String obj = targetsStr.substring(objStart + 1, objEnd);

			// Parse time
			int timeIdx = obj.indexOf("\"time\":");
			if (timeIdx != -1)
			{
				int timeStart = timeIdx + 7;
				int timeEnd = obj.indexOf(',', timeStart);
				if (timeEnd == -1)
					timeEnd = obj.length();
				String timeStr = obj.substring(timeStart, timeEnd);
				timeStr.trim();
				if (timeStr.startsWith("\""))
					timeStr = timeStr.substring(1, timeStr.length() - 1);
				long targetTime = parseTimeToSeconds(timeStr);
				targetTime = max(0L, min(86400L, targetTime));

				// Parse value
				int valueIdx = obj.indexOf("\"value\":");
				if (valueIdx != -1)
				{
					int valueStart = valueIdx + 8;
					int valueEnd = obj.indexOf(',', valueStart);
					if (valueEnd == -1)
						valueEnd = obj.length();
					String valueStr = obj.substring(valueStart, valueEnd);
					valueStr.trim();
					int value = valueStr.toInt();
					value = max(0, min(100, value));
					uint8_t finalValue = (uint8_t)value;

					Target t;
					t.Time = targetTime;
					t.Value = finalValue;
					_aqc->_PwmChannels[channel].addTarget(t);
				}
			}

			pos = objEnd + 1;
		}
	}

	// Persist to SD card
	_aqc->writeLedConfig(channel);
	_aqc->_IsFirstCycle = true;

	char buf[64];
	sprintf(buf, "{\"status\":\"ok\",\"channel\":%u,\"target_count\":%u}",
			channel, _aqc->_PwmChannels[channel].TargetCount);

	Serial.print(F("Schedule saved for channel "));
	Serial.print(channel);
	Serial.print(F(": "));
	Serial.print(_aqc->_PwmChannels[channel].TargetCount);
	Serial.println(F(" targets"));

	_Server.send(200, "application/json", buf);
}

// API: POST /api/schedule/clear - Clears all schedules from all channels
void handleApiScheduleClear()
{
	Serial.println(F("Clearing all schedules..."));

	// Clear all targets from all 6 visible channels
	for (uint8_t channel = 0; channel < 6; channel++)
	{
		// Remove all targets from this channel
		while (_aqc->_PwmChannels[channel].TargetCount > 0)
		{
			_aqc->_PwmChannels[channel].removeTargetAt(0);
		}

		// Also clear the SD card config file for this channel
		char sTempFilename[30];
		String sPwmFilename = "config/ledch_";
		sPwmFilename += (channel <= 9 ? (String("0") + String(channel)) : String(channel));
		sPwmFilename += ".cfg";
		sPwmFilename.toCharArray(sTempFilename, 30);

		if (SD.exists(sTempFilename))
		{
			if (SD.remove(sTempFilename))
			{
				Serial.print(F("Deleted config file: "));
				Serial.println(sPwmFilename);
			}
			else
			{
				Serial.print(F("Failed to delete: "));
				Serial.println(sPwmFilename);
			}
		}
	}

	_aqc->_IsFirstCycle = true;
	Serial.println(F("✅ All schedules cleared"));

	_Server.send(200, "application/json", "{\"status\":\"ok\",\"message\":\"All schedules cleared\"}");
}

// API: POST /api/schedule/target/add
void handleApiTargetAdd()
{
	String body = _Server.arg("plain");
	Serial.print(F("Add target body: "));
	Serial.println(body);
	// Parse channel/time/value from JSON body, with query-arg fallback
	uint8_t channel = 0;
	long targetTime = 0;
	uint8_t finalValue = 0;

	if (body.length() > 0)
	{
		// Parse channel
		int channelIdx = body.indexOf("\"channel\":");
		if (channelIdx == -1)
		{
			_Server.send(400, "application/json", "{\"error\":\"Missing channel\"}");
			return;
		}
		int channelStart = channelIdx + 10;
		int channelEnd = body.indexOf(',', channelStart);
		String channelStr = body.substring(channelStart, channelEnd);
		channelStr.trim();
		channel = channelStr.toInt();

		// Parse time
		int timeIdx = body.indexOf("\"time\":");
		if (timeIdx == -1)
		{
			_Server.send(400, "application/json", "{\"error\":\"Missing time\"}");
			return;
		}
		int timeStart = timeIdx + 7;
		int timeEnd = body.indexOf(',', timeStart);
		if (timeEnd == -1)
			timeEnd = body.indexOf('}', timeStart);
		String timeStr = body.substring(timeStart, timeEnd);
		timeStr.trim();
		if (timeStr.startsWith("\""))
			timeStr = timeStr.substring(1, timeStr.length() - 1);
		targetTime = parseTimeToSeconds(timeStr);
		targetTime = max(0L, min(86400L, targetTime));

		// Parse value
		int valueIdx = body.indexOf("\"value\":");
		if (valueIdx == -1)
		{
			_Server.send(400, "application/json", "{\"error\":\"Missing value\"}");
			return;
		}
		int valueStart = valueIdx + 8;
		int valueEnd = body.indexOf(',', valueStart);
		if (valueEnd == -1)
			valueEnd = body.indexOf('}', valueStart);
		String valueStr = body.substring(valueStart, valueEnd);
		valueStr.trim();
		int value = valueStr.toInt();
		value = max(0, min(100, value));
		finalValue = (uint8_t)value;
	}
	else
	{
		// Fallback to query arguments
		if (!_Server.hasArg("channel") || !_Server.hasArg("time") || !_Server.hasArg("value"))
		{
			_Server.send(400, "application/json", "{\"error\":\"Missing parameters\"}");
			return;
		}
		channel = _Server.arg("channel").toInt();
		targetTime = parseTimeToSeconds(_Server.arg("time"));
		targetTime = max(0L, min(86400L, targetTime));
		int v = _Server.arg("value").toInt();
		v = max(0, min(100, v));
		finalValue = (uint8_t)v;
	}

	if (channel >= 6)
	{
		_Server.send(400, "application/json", "{\"error\":\"Invalid channel\"}");
		return;
	}

	// Remove existing target at same time if present
	for (uint8_t i = 0; i < _aqc->_PwmChannels[channel].TargetCount; i++)
	{
		if (_aqc->_PwmChannels[channel].Targets[i].Time == targetTime)
		{
			_aqc->_PwmChannels[channel].removeTargetAt(i);
			break;
		}
	}

	// Add new target
	Target t;
	t.Time = targetTime;
	t.Value = finalValue;
	_aqc->_PwmChannels[channel].addTarget(t);

	// Persist to SD
	_aqc->writeLedConfig(channel);
	_aqc->_IsFirstCycle = true;

	Serial.print(F("Added target: ch="));
	Serial.print(channel);
	Serial.print(F(", time="));
	Serial.print(targetTime);
	Serial.print(F(", value="));
	Serial.println(finalValue);

	_Server.send(200, "application/json", "{\"success\":true}");
}

// API: POST /api/schedule/target/delete
void handleApiTargetDelete()
{
	String body = _Server.arg("plain");

	// Parse channel
	int channelIdx = body.indexOf("\"channel\":");
	if (channelIdx == -1)
	{
		_Server.send(400, "application/json", "{\"error\":\"Missing channel\"}");
		return;
	}
	int channelStart = channelIdx + 10;
	int channelEnd = body.indexOf(',', channelStart);
	String channelStr = body.substring(channelStart, channelEnd);
	channelStr.trim();
	uint8_t channel = channelStr.toInt();

	// Parse time
	int timeIdx = body.indexOf("\"time\":");
	if (timeIdx == -1)
	{
		_Server.send(400, "application/json", "{\"error\":\"Missing time\"}");
		return;
	}
	int timeStart = timeIdx + 7;
	int timeEnd = body.indexOf(',', timeStart);
	if (timeEnd == -1)
		timeEnd = body.indexOf('}', timeStart);
	String timeStr = body.substring(timeStart, timeEnd);
	timeStr.trim();
	if (timeStr.startsWith("\""))
		timeStr = timeStr.substring(1, timeStr.length() - 1);
	long targetTime = parseTimeToSeconds(timeStr);

	// Find and remove target
	for (uint8_t i = 0; i < _aqc->_PwmChannels[channel].TargetCount; i++)
	{
		if (_aqc->_PwmChannels[channel].Targets[i].Time == targetTime)
		{
			_aqc->_PwmChannels[channel].removeTargetAt(i);
			break;
		}
	}

	// Persist to SD
	_aqc->writeLedConfig(channel);
	_aqc->_IsFirstCycle = true;

	_Server.send(200, "application/json", "{\"status\":\"ok\"}");
}

// API: POST /api/test/start
void handleApiTestStart()
{
	for (uint8_t i = 0; i < 6; i++)
	{
		_aqc->_PwmChannels[i].TestMode = true;
		_aqc->_PwmChannels[i].TestModeSetTime = _aqc->CurrentSecOfDay;
	}
	Serial.println(F("Test mode STARTED"));
	_Server.send(200, "application/json", "{\"status\":\"ok\",\"test_mode\":true}");
}

// API: POST /api/test/update
void handleApiTestUpdate()
{
	String body = _Server.arg("plain");

	// Support two payload formats:
	// 1. {channel: N, value: V} - update single channel
	// 2. {values: [v0,v1,v2,v3,v4,v5]} - update all channels

	if (body.indexOf("\"values\":[") != -1)
	{
		// Format 2: array of values
		int arrayStart = body.indexOf("\"values\":[") + 10;
		int arrayEnd = body.indexOf(']', arrayStart);
		String valuesStr = body.substring(arrayStart, arrayEnd);

		uint8_t ch = 0;
		unsigned int pos = 0;
		while (pos < valuesStr.length() && ch < 6)
		{
			int nextComma = valuesStr.indexOf(',', pos);
			if (nextComma == -1)
				nextComma = valuesStr.length();
			String valueStr = valuesStr.substring(pos, nextComma);
			valueStr.trim();
			int value = valueStr.toInt();
			value = max(0, min(100, value));
			_aqc->_PwmChannels[ch].TestValue = (uint8_t)value;
			_aqc->_PwmChannels[ch].TestModeSetTime = _aqc->CurrentSecOfDay;
			ch++;
			pos = nextComma + 1;
		}
	}
	else
	{
		// Format 1: single channel
		int channelIdx = body.indexOf("\"channel\":");
		int valueIdx = body.indexOf("\"value\":");

		if (channelIdx != -1 && valueIdx != -1)
		{
			int channelStart = channelIdx + 10;
			int channelEnd = body.indexOf(',', channelStart);
			String channelStr = body.substring(channelStart, channelEnd);
			channelStr.trim();
			uint8_t channel = channelStr.toInt();

			int valueStart = valueIdx + 8;
			int valueEnd = body.indexOf(',', valueStart);
			if (valueEnd == -1)
				valueEnd = body.indexOf('}', valueStart);
			String valueStr = body.substring(valueStart, valueEnd);
			valueStr.trim();
			int value = valueStr.toInt();
			value = max(0, min(100, value));

			if (channel < 6)
			{
				_aqc->_PwmChannels[channel].TestValue = (uint8_t)value;
				_aqc->_PwmChannels[channel].TestModeSetTime = _aqc->CurrentSecOfDay;
			}
		}
	}

	_Server.send(200, "application/json", "{\"status\":\"ok\"}");
}

// API: POST /api/test/exit
void handleApiTestExit()
{
	for (uint8_t i = 0; i < 6; i++)
	{
		_aqc->_PwmChannels[i].TestMode = false;
	}
	Serial.println(F("Test mode EXITED"));
	_Server.send(200, "application/json", "{\"status\":\"ok\",\"test_mode\":false}");
}

// API: GET /api/macro/list
void handleApiMacroList()
{
	// List all macro files from macros/ directory
	_Server.setContentLength(CONTENT_LENGTH_UNKNOWN);
	_Server.send(200, "application/json", "");

	_Server.sendContent("{\"macros\":[");

	// Enumerate macro files: check for pattern macros/macro_NNN_ch00.cfg
	// This identifies all macros by checking the first channel file
	bool firstMacro = true;
	for (uint16_t macroNum = 1; macroNum <= 999; macroNum++)
	{
		char sTempFilename[50];
		String sMacroPath = "macros/macro_";
		sMacroPath += (macroNum <= 9 ? "00" : (macroNum <= 99 ? "0" : ""));
		sMacroPath += String(macroNum);
		sMacroPath += "_ch00.cfg";
		sMacroPath.toCharArray(sTempFilename, 50);

		if (SD.exists(sTempFilename))
		{
			if (!firstMacro)
				_Server.sendContent(",");
			firstMacro = false;

			// Build macro ID (e.g., "macro_001")
			char idBuf[64];
			String macroIdStr = sMacroPath.substring(7, sMacroPath.indexOf("_ch"));
			sprintf(idBuf, "{\"id\":\"%s\",\"name\":\"%s\"}", macroIdStr.c_str(), macroIdStr.c_str());
			_Server.sendContent(idBuf);
		}
	}

	_Server.sendContent("]}");
}

// API: GET /api/macro/get?id=xxx
void handleApiMacroGet()
{
	String macroId = _Server.arg("id");

	if (macroId.length() == 0)
	{
		_Server.send(400, "application/json", "{\"error\":\"Missing macro id\"}");
		return;
	}

	// Try to load macro targets for all 6 channels
	_Server.setContentLength(CONTENT_LENGTH_UNKNOWN);
	_Server.send(200, "application/json", "");

	char buf[48];
	sprintf(buf, "{\"id\":\"");
	_Server.sendContent(buf);
	_Server.sendContent(macroId);
	_Server.sendContent("\",\"channels\":[");

	for (uint8_t ch = 0; ch < 6; ch++)
	{
		if (ch > 0)
			_Server.sendContent(",");

		sprintf(buf, "{\"channel\":%u,\"targets\":[", ch);
		_Server.sendContent(buf);

		// Try to read macro file
		char sTempFilename[50];
		String sMacroPath = "macros/";
		sMacroPath += macroId;
		sMacroPath += "_ch";
		sMacroPath += (ch <= 9 ? (String("0") + String(ch)) : String(ch));
		sMacroPath += ".cfg";
		sMacroPath.toCharArray(sTempFilename, 50);

		File macroFile = SD.open(sTempFilename);
		if (macroFile)
		{
			bool targetFirst = true;
			while (macroFile.available())
			{
				String sLine = macroFile.readStringUntil(10);
				if (sLine.length() > 0 && sLine.charAt(sLine.length() - 1) == 13)
				{
					sLine = sLine.substring(0, sLine.length() - 1);
				}
				if (sLine.length() == 0 || sLine.startsWith("//"))
					continue;

				int semiIdx = sLine.indexOf(';');
				if (semiIdx == -1)
					continue;

				String timeStr = sLine.substring(0, semiIdx);
				String valueStr = sLine.substring(semiIdx + 1);

				int colonIdx = timeStr.indexOf(':');
				long timeVal = 0;
				if (colonIdx != -1)
				{
					int mins = timeStr.substring(0, colonIdx).toInt();
					int secs = timeStr.substring(colonIdx + 1).toInt();
					timeVal = (mins * 60) + secs;
				}
				else
				{
					timeVal = timeStr.toInt();
				}

				int value = valueStr.toInt();
				value = max(0, min(100, value));

				if (!targetFirst)
					_Server.sendContent(",");
				targetFirst = false;

				sprintf(buf, "{\"time\":%ld,\"value\":%d}", timeVal, value);
				_Server.sendContent(buf);
			}
			macroFile.close();
		}

		_Server.sendContent("]}");
	}

	_Server.sendContent("]}");
}

// API: POST /api/macro/save
void handleApiMacroSave()
{
	String body = _Server.arg("plain");

	// Parse macro id (user-provided name)
	int idIdx = body.indexOf("\"id\":");
	if (idIdx == -1)
	{
		_Server.send(400, "application/json", "{\"error\":\"Missing id\"}");
		return;
	}

	int idStart = idIdx + 5;
	int idEnd = body.indexOf(',', idStart);
	if (idEnd == -1)
		idEnd = body.indexOf('}', idStart);
	String userMacroId = body.substring(idStart, idEnd);
	userMacroId.trim();
	if (userMacroId.startsWith("\""))
		userMacroId = userMacroId.substring(1, userMacroId.length() - 1);

	if (userMacroId.length() == 0)
	{
		_Server.send(400, "application/json", "{\"error\":\"Invalid id\"}");
		return;
	}

	// Generate normalized macro ID: find next available macro_NNN
	uint16_t macroNum = 1;
	String normalizedMacroId;
	char sTempFilename[50];

	// Find first available macro number
	while (macroNum <= 999)
	{
		normalizedMacroId = "macro_";
		normalizedMacroId += (macroNum <= 9 ? "00" : (macroNum <= 99 ? "0" : ""));
		normalizedMacroId += String(macroNum);

		String checkPath = "macros/";
		checkPath += normalizedMacroId;
		checkPath += "_ch00.cfg";
		checkPath.toCharArray(sTempFilename, 50);

		// If this macro already exists, use it (edit mode); otherwise keep looking for next available
		if (!SD.exists(sTempFilename))
		{
			break; // Found an available slot
		}
		macroNum++;
	}

	// Use normalized ID for file storage
	String macroId = normalizedMacroId;

	// Parse channels array
	int channelsIdx = body.indexOf("\"channels\":[");
	if (channelsIdx == -1)
	{
		_Server.send(400, "application/json", "{\"error\":\"Missing channels\"}");
		return;
	}

	int arrayStart = channelsIdx + 12;
	int arrayEnd = body.indexOf(']', arrayStart);
	String channelsStr = body.substring(arrayStart, arrayEnd);

	// Save each channel's targets
	uint8_t channel = 0;
	unsigned int pos = 0;

	while (pos < channelsStr.length() && channel < 6)
	{
		int objStart = channelsStr.indexOf('{', pos);
		if (objStart == -1)
			break;
		int objEnd = channelsStr.indexOf('}', objStart);
		if (objEnd == -1)
			break;

		String obj = channelsStr.substring(objStart + 1, objEnd);

		// Parse targets array from object
		int targetsIdx = obj.indexOf("\"targets\":[");
		if (targetsIdx != -1)
		{
			int targetsStart = targetsIdx + 11;
			int targetsEnd = obj.indexOf(']', targetsStart);
			String targetsStr = obj.substring(targetsStart, targetsEnd);

			// Create temp channel to store targets
			PwmChannel tempChannel;
			tempChannel.TargetCount = 0;

			// Parse target objects
			unsigned int tPos = 0;
			while (tPos < targetsStr.length() && tempChannel.TargetCount < MAX_TARGET_COUNT_PER_CHANNEL)
			{
				int tObjStart = targetsStr.indexOf('{', tPos);
				if (tObjStart == -1)
					break;
				int tObjEnd = targetsStr.indexOf('}', tObjStart);
				if (tObjEnd == -1)
					break;

				String tObj = targetsStr.substring(tObjStart + 1, tObjEnd);

				// Parse time
				int timeIdx = tObj.indexOf("\"time\":");
				int valueIdx = tObj.indexOf("\"value\":");

				if (timeIdx != -1 && valueIdx != -1)
				{
					int timeStart = timeIdx + 7;
					int timeEnd = tObj.indexOf(',', timeStart);
					if (timeEnd == -1)
						timeEnd = tObj.indexOf('}', timeStart);
					String timeStr = tObj.substring(timeStart, timeEnd);
					timeStr.trim();
					long timeVal = timeStr.toInt();
					timeVal = max(0L, min(86400L, timeVal));

					int valueStart = valueIdx + 8;
					int valueEnd = tObj.indexOf(',', valueStart);
					if (valueEnd == -1)
						valueEnd = tObj.indexOf('}', valueStart);
					String valueStr = tObj.substring(valueStart, valueEnd);
					valueStr.trim();
					int val = valueStr.toInt();
					val = max(0, min(100, val));

					Target t;
					t.Time = timeVal;
					t.Value = (uint8_t)val;
					tempChannel.addTarget(t);
				}

				tPos = tObjEnd + 1;
			}

			// Write macro file for this channel
			{
				// Format macro path without String concatenation to avoid heap fragmentation
				char sTempMacroPath[50];
				sprintf(sTempMacroPath, "macros/%s_ch%02d.cfg", macroId.c_str(), channel);

				// Delete old file if it exists
				if (SD.exists(sTempMacroPath))
				{
					if (!SD.remove(sTempMacroPath))
					{
						Serial.print(F("Error: Couldn't remove old macro file "));
						Serial.println(sTempMacroPath);
						continue;
					}
				}

				// Create new file
				File configFile = SD.open(sTempMacroPath, FILE_WRITE);
				if (!configFile)
				{
					Serial.print(F("Error: Couldn't create macro file "));
					Serial.println(sTempMacroPath);
					continue;
				}

				// Write all targets to file (same format as schedules)
				for (uint8_t t = 0; t < tempChannel.TargetCount; t++)
				{
					Target tTarget = tempChannel.Targets[t];

					// Format time as MM:SS for macro (duration-based, not 24h)
					uint8_t iMin = tTarget.Time / 60;
					uint8_t iSec = tTarget.Time % 60;

					char timeBuf[8];
					sprintf(timeBuf, "%02d:%02d", iMin, iSec);
					configFile.print(timeBuf);

					configFile.write(';');
					char valueBuf[4];
					sprintf(valueBuf, "%u", (unsigned int)tTarget.Value);
					configFile.print(valueBuf);

					configFile.write(13);
					configFile.write(10);
				}

				configFile.close();
			}
		}

		channel++;
		pos = objEnd + 1;
	}

	Serial.print(F("✅ Macro saved: "));
	Serial.println(macroId);

	char buf[64];
	sprintf(buf, "{\"status\":\"ok\",\"id\":\"%s\"}", macroId.c_str());
	_Server.send(200, "application/json", buf);
}

// API: POST /api/macro/activate
void handleApiMacroActivate()
{
	String body = _Server.arg("plain");

	// Parse macro id
	int idIdx = body.indexOf("\"id\":");
	if (idIdx == -1)
	{
		_Server.send(400, "application/json", "{\"error\":\"Missing id\"}");
		return;
	}

	int idStart = idIdx + 5;
	int idEnd = body.indexOf(',', idStart);
	if (idEnd == -1)
		idEnd = body.indexOf('}', idStart);
	String macroId = body.substring(idStart, idEnd);
	macroId.trim();
	if (macroId.startsWith("\""))
		macroId = macroId.substring(1, macroId.length() - 1);

	// Parse duration from JSON body
	int durIdx = body.indexOf("\"duration\":");
	uint32_t duration = 0;
	if (durIdx != -1)
	{
		int durStart = durIdx + 11;
		int durEnd = body.indexOf(',', durStart);
		if (durEnd == -1)
			durEnd = body.indexOf('}', durStart);
		String durStr = body.substring(durStart, durEnd);
		durStr.trim();
		duration = durStr.toInt();
	}

	// Activate macro
	if (_aqc->activateMacro(macroId, duration))
	{
		// Build JSON response
		char response[100];
		sprintf(response, "{\"status\":\"ok\",\"expires_in\":%lu}", (unsigned long)duration);
		_Server.send(200, "application/json", response);

		Serial.print(F("🎬 Macro activated: "));
		Serial.print(macroId);
		Serial.print(F(", duration: "));
		Serial.print(duration);
		Serial.println(F("s"));
	}
	else
	{
		_Server.send(500, "application/json", "{\"error\":\"Activation failed\"}");
	}
}

// API: POST /api/macro/stop
void handleApiMacroStop()
{
	if (_aqc->isMacroActive())
	{
		_aqc->restoreSchedule();
		_Server.send(200, "application/json", "{\"status\":\"ok\"}");
		Serial.println(F("🛑 Macro stopped manually"));
	}
	else
	{
		_Server.send(400, "application/json", "{\"error\":\"No macro active\"}");
	}
}

// API: POST /api/macro/delete
void handleApiMacroDelete()
{
	String body = _Server.arg("plain");

	// Parse macro id
	int idIdx = body.indexOf("\"id\":");
	if (idIdx == -1)
	{
		_Server.send(400, "application/json", "{\"error\":\"Missing id\"}");
		return;
	}

	int idStart = idIdx + 5;
	int idEnd = body.indexOf(',', idStart);
	if (idEnd == -1)
		idEnd = body.indexOf('}', idStart);
	String macroId = body.substring(idStart, idEnd);
	macroId.trim();
	if (macroId.startsWith("\""))
		macroId = macroId.substring(1, macroId.length() - 1);

	if (macroId.length() == 0)
	{
		_Server.send(400, "application/json", "{\"error\":\"Invalid id\"}");
		return;
	}

	// Delete macro files for all channels
	for (uint8_t ch = 0; ch < 6; ch++)
	{
		char sTempFilename[50];
		String sMacroPath = "macros/";
		sMacroPath += macroId;
		sMacroPath += "_ch";
		sMacroPath += (ch <= 9 ? (String("0") + String(ch)) : String(ch));
		sMacroPath += ".cfg";
		sMacroPath.toCharArray(sTempFilename, 50);

		if (SD.exists(sTempFilename))
		{
			if (SD.remove(sTempFilename))
			{
				Serial.print(F("Deleted macro file: "));
				Serial.println(sMacroPath);
			}
		}
	}

	Serial.print(F("🗑️  Macro deleted: "));
	Serial.println(macroId);

	_Server.send(200, "application/json", "{\"status\":\"ok\"}");
}

// API: POST /api/reboot
void handleApiReboot()
{
	Serial.println(F("Reboot requested via API"));
	_Server.send(200, "application/json", "{\"status\":\"rebooting\"}");
	delay(500); // Give time for response to be sent
	ESP.restart();
}

// API: GET /api/debug - Returns heap/memory diagnostics
void handleApiDebug()
{
	uint32_t freeHeap = ESP.getFreeHeap();
	uint32_t maxFreeBlock = ESP.getMaxFreeBlockSize();
	float fragmentation = 0.0;
	if (freeHeap > 0)
		fragmentation = 100.0 * (1.0 - (float)maxFreeBlock / (float)freeHeap);

	// Stream JSON using char buffers - NO String objects
	_Server.setContentLength(CONTENT_LENGTH_UNKNOWN);
	_Server.send(200, "application/json", "");

	char buf[16];

	_Server.sendContent("{\"free_heap\":");
	sprintf(buf, "%lu", (unsigned long)freeHeap);
	_Server.sendContent(buf);

	_Server.sendContent(",\"max_free_block\":");
	sprintf(buf, "%lu", (unsigned long)maxFreeBlock);
	_Server.sendContent(buf);

	_Server.sendContent(",\"heap_fragmentation\":");
	dtostrf(fragmentation, 1, 1, buf);
	_Server.sendContent(buf);

	_Server.sendContent(",\"uptime_ms\":");
	sprintf(buf, "%lu", millis());
	_Server.sendContent(buf);

	_Server.sendContent(",\"vcc_voltage_mv\":");
	sprintf(buf, "%u", ESP.getVcc());
	_Server.sendContent(buf);

	_Server.sendContent(",\"cpu_freq_mhz\":");
	sprintf(buf, "%u", ESP.getCpuFreqMHz());
	_Server.sendContent(buf);

	_Server.sendContent("}");

	// Also log to serial
	Serial.print(F("DEBUG: Free="));
	Serial.print(freeHeap);
	Serial.print(F("B MaxBlock="));
	Serial.print(maxFreeBlock);
	Serial.print(F("B Frag="));
	Serial.print(fragmentation, 1);
	Serial.println(F("%"));
}

// File upload handler - receives file chunks
// Note: Global variables are safe here because ESP8266WebServer is single-threaded
static File _uploadFile;		// Persists across upload chunks
static String _uploadPath = ""; // Stores target path from form data

void handleUpload()
{
	HTTPUpload &upload = _Server.upload();

	if (upload.status == UPLOAD_FILE_START)
	{
		// Get the target path from form data
		_uploadPath = _Server.arg("path");

		if (_uploadPath.length() == 0)
		{
			Serial.println(F("Upload error: No path specified"));
			return;
		}

		// Remove leading slash if present
		if (_uploadPath.startsWith("/"))
		{
			_uploadPath = _uploadPath.substring(1);
		}

		Serial.print(F("📤 Upload started: "));
		Serial.println(_uploadPath);

		// Delete existing file if present
		if (SD.exists(_uploadPath.c_str()))
		{
			SD.remove(_uploadPath.c_str());
			Serial.print(F("  Removed existing file: "));
			Serial.println(_uploadPath);
		}

		// Note: SD library doesn't support mkdir, so directories must exist
		// Users should manually create directory structure on SD card before upload
		// or use the web interface to create necessary folders

		// Open file for writing
		_uploadFile = SD.open(_uploadPath.c_str(), FILE_WRITE);
		if (!_uploadFile)
		{
			Serial.print(F("❌ Failed to open file for writing: "));
			Serial.println(_uploadPath);
			Serial.println(F("  Ensure parent directory exists on SD card"));
		}
	}
	else if (upload.status == UPLOAD_FILE_WRITE)
	{
		// Write chunk to file
		if (_uploadFile)
		{
			size_t written = _uploadFile.write(upload.buf, upload.currentSize);
			if (written != upload.currentSize)
			{
				Serial.print(F("⚠️  Write size mismatch: expected "));
				Serial.print(upload.currentSize);
				Serial.print(F(", wrote "));
				Serial.println(written);
				// Close file and abort upload on write error
				_uploadFile.close();
				// Explicitly invalidate the file object to prevent further writes
				_uploadFile = File();
				Serial.println(F("❌ Upload aborted due to write error"));
			}
		}
		else
		{
			Serial.println(F("❌ File not open for writing"));
		}
	}
	else if (upload.status == UPLOAD_FILE_END)
	{
		// Close file
		if (_uploadFile)
		{
			_uploadFile.close();
			Serial.print(F("✓ Upload complete: "));
			Serial.print(_uploadPath);
			Serial.print(F(" ("));
			Serial.print(upload.totalSize);
			Serial.println(F(" bytes)"));
		}
		else
		{
			Serial.println(F("❌ File was not open at upload end"));
		}
	}
	else if (upload.status == UPLOAD_FILE_ABORTED)
	{
		if (_uploadFile)
		{
			_uploadFile.close();
		}
		Serial.println(F("❌ Upload aborted"));
		_uploadPath = "";
	}
}

// Upload completion handler - sends JSON response
void handleUploadComplete()
{
	// Use the path stored during upload process (more reliable than re-reading form data)
	String targetPath = _uploadPath;

	if (targetPath.length() == 0)
	{
		// Fallback to form data if upload path wasn't set
		targetPath = _Server.arg("path");
		if (targetPath.startsWith("/"))
		{
			targetPath = targetPath.substring(1);
		}
	}

	if (targetPath.length() == 0)
	{
		_Server.send(400, "application/json", "{\"success\":false,\"error\":\"No path specified\"}");
		Serial.println(F("❌ Upload failed: No path specified"));
		return;
	}

	// Verify file was created successfully
	if (SD.exists(targetPath.c_str()))
	{
		File f = SD.open(targetPath.c_str(), FILE_READ);
		if (f)
		{
			size_t fileSize = f.size();
			f.close();

			// Send success response with minimal String usage
			_Server.setContentLength(CONTENT_LENGTH_UNKNOWN);
			_Server.send(200, "application/json", "");

			_Server.sendContent("{\"success\":true,\"path\":\"");
			_Server.sendContent(targetPath);
			_Server.sendContent("\",\"size\":");

			char buf[16];
			snprintf(buf, sizeof(buf), "%u", (unsigned int)fileSize);
			_Server.sendContent(buf);
			_Server.sendContent("}");

			Serial.print(F("✅ Upload confirmed: "));
			Serial.print(targetPath);
			Serial.print(F(" ("));
			Serial.print(fileSize);
			Serial.println(F(" bytes)"));
		}
		else
		{
			_Server.send(500, "application/json", "{\"success\":false,\"error\":\"File created but cannot be read\"}");
			Serial.println(F("❌ File created but cannot be read"));
		}
	}
	else
	{
		_Server.send(500, "application/json", "{\"success\":false,\"error\":\"File upload failed\"}");
		Serial.print(F("❌ Upload failed: File not found after upload: "));
		Serial.println(targetPath);
	}

	// Reset upload state
	_uploadPath = "";
}

// API: POST /api/time/set
void handleApiTimeSet()
{
#if defined(USE_RTC_DS3231)
	String body = _Server.arg("plain");
	Serial.print(F("Time set request body: "));
	Serial.println(body);

	// Helper lambda: Parse JSON integer field
	auto parseTimeField = [&body](const char *field) -> int
	{
		int idx = body.indexOf(field);
		if (idx == -1)
			return -1;
		int start = idx + strlen(field) + 1;
		int end = body.indexOf(',', start);
		if (end == -1)
			end = body.indexOf('}', start);
		return body.substring(start, end).toInt();
	};

	// Parse time fields
	int hour = parseTimeField("\"hour\":");
	int minute = parseTimeField("\"minute\":");
	int second = parseTimeField("\"second\":");

	if (hour == -1 || minute == -1 || second == -1)
	{
		_Server.send(400, "application/json", "{\"error\":\"Missing or invalid time field (hour/minute/second)\"}");
		return;
	}

	// Validate ranges
	if (hour < 0 || hour > 23 || minute < 0 || minute > 59 || second < 0 || second > 59)
	{
		_Server.send(400, "application/json", "{\"error\":\"Invalid time values (hour: 0-23, minute: 0-59, second: 0-59)\"}");
		return;
	}

	// Create tmElements_t struct from input, preserving current date
	tmElements_t tm;
	tm.Hour = hour;
	tm.Minute = minute;
	tm.Second = second;
	tm.Day = day(); // Preserve current date
	tm.Month = month();
	tm.Year = year() - 1970;

	// Convert to time_t and write to RTC
	time_t t = makeTime(tm);
	RTC.set(t);

	// Sync system time with RTC
	setSyncProvider(getRTCTime);
	if (timeStatus() != timeSet)
	{
		Serial.print(F("ERROR: RTC sync failed, timeStatus="));
		Serial.println(timeStatus());
		_Server.send(500, "application/json", "{\"error\":\"RTC sync failed - time not set\"}");
		return;
	}

	// Update time sync tracking
	_aqc->_LastTimeSync = now();
	_aqc->_LastTimeSyncSource = TimeSyncSource::Api;
	_aqc->_NtpSyncFailed = false; // Clear the flag since browser provided time

	// Stream JSON response with updated time
	_Server.setContentLength(CONTENT_LENGTH_UNKNOWN);
	_Server.send(200, "application/json", "");

	char buf[16];
	_Server.sendContent("{\"status\":\"ok\",\"time\":\"");
	sprintf(buf, "%02d:%02d:%02d", hour, minute, second);
	_Server.sendContent(buf);
	_Server.sendContent("\"}");

	Serial.print(F("✅ Time set to: "));
	Serial.print(hour);
	Serial.print(F(":"));
	Serial.print(minute);
	Serial.print(F(":"));
	Serial.println(second);
	Serial.println(F("Time sync source: API"));
#else
	_Server.send(501, "application/json", "{\"error\":\"RTC not available\"}");
#endif
}

#endif