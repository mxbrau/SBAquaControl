/*
Aqua Control Library

Creationdate: 2016-12-28
Created by Marcel Schulz (Schullebernd)

Further information on www.schullebernd.de

Copyright 2016
*/

#ifndef __AQUACONTROL_H_
#define __AQUACONTROL_H_

#include "AquaControl_config.h"

#define AQC_VERSION "0.5"
#define AQC_BUILD "0.5.001"

#include <Arduino.h>

#if defined(ESP8266)
#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <ESP8266WebServer.h>
#include <ESP8266mDNS.h>
#include <ArduinoOTA.h> // Over-The-Air updates
#endif

#if defined(USE_RTC_DS3231)
#include <Wire.h>
#include <DS3232RTC.h>
#endif

#if defined(USE_DS18B20_TEMP_SENSOR)
#include <OneWire.h>
#define DS18B20_PIN D4 // Defines the pin, where the data wire of the DS18B20 sensor is connected
#endif

#if defined(USE_PCA9685)
#include <Adafruit_PWMServoDriver.h>
#define PWM_FREQ 300
#endif

// This is for the sd card modul
#include <SPI.h>
#include <SD.h>

#include <TimeLib.h>

#if defined(USE_WEBSERVER)
// Webserver handlers
void handleRoot();
void handleNotFound();
void handleUpload();
void handleUploadComplete();

// JSON API handlers
void handleApiStatus();
void handleApiScheduleGet();
void handleApiScheduleAll();
void handleApiScheduleSave();
void handleApiScheduleClear();
void handleApiTargetAdd();
void handleApiTargetDelete();
void handleApiTestStart();
void handleApiTestUpdate();
void handleApiTestExit();
void handleApiMacroList();
void handleApiMacroGet();
void handleApiMacroSave();
void handleApiMacroActivate();
void handleApiMacroStop();
void handleApiMacroDelete();
void handleApiReboot();
void handleApiDebug();
void handleApiTimeSet();
void handleApiChannelConfigGet();
void handleApiChannelConfigSave();
#endif

#if defined(__AVR__)
#define SD_CS 0
#elif defined(ESP8266)
#define SD_CS D8
#else
#define SD_CS TODO
#endif

#if defined(USE_PCA9685)
#define PWM_STEP 5
#define PWM_MAX 4095 // 12 bit PCA9685 Board
/* Defines the maximum number of supported pwm channels. This is restriced by the PCA9685 controller */
#define PWM_CHANNELS 16
#define PWM_CHANNEL_0 0
#define PWM_CHANNEL_1 1
#define PWM_CHANNEL_2 2
#define PWM_CHANNEL_3 3
#define PWM_CHANNEL_4 4
#define PWM_CHANNEL_5 5
#define PWM_CHANNEL_6 6
#define PWM_CHANNEL_7 7
#define PWM_CHANNEL_8 8
#define PWM_CHANNEL_9 9
#define PWM_CHANNEL_10 10
#define PWM_CHANNEL_11 11
#define PWM_CHANNEL_12 12
#define PWM_CHANNEL_13 13
#define PWM_CHANNEL_14 14
#define PWM_CHANNEL_15 15
#elif defined(__AVR__) // defined(USE_PCA9685)
#define PWM_STEP 1
#define PWM_MAX 255 // AVR or Arduino has only 8 bit PWM output
#define PWM_CHANNEL_0 5
#define PWM_CHANNEL_1 9
#define PWM_CHANNEL_2 3
#define PWM_CHANNEL_3 6
#define PWM_CHANNEL_4 10
#define PWM_CHANNEL_5 11
#if defined(__AVR_ATmega2560__)
/* Defines the maximum number of supported pwm channels. This is restriced by the PCA9685 controller */
#define PWM_CHANNELS 16
#define PWM_CHANNEL_6 4
#define PWM_CHANNEL_7 2
#define PWM_CHANNEL_8 7
#define PWM_CHANNEL_9 8
#define PWM_CHANNEL_10 12
#define PWM_CHANNEL_11 13
#define PWM_CHANNEL_12 44
#define PWM_CHANNEL_13 45
#define PWM_CHANNEL_14 46
#define PWM_CHANNEL_15 47
#else
/* Defines the maximum number of supported pwm channels. This is restriced by the PCA9685 controller */
#define PWM_CHANNELS 6
#endif // defined(__AVR_ATmega2560__)
#elif defined(ESP8266)
#define PWM_STEP 4
#define PWM_MAX 1023 // ESP8266 has software PWM output with 10 bit precision
#define PWM_CHANNEL_0 D0
#define PWM_CHANNEL_1 D3
/* Defines the maximum number of supported pwm channels. This is restriced by the PCA9685 controller */
#define PWM_CHANNELS 2
#else // elif defined(ESP8266)
#define PWM_STEP 1
#define PWM_MAX 255 // Asume a 8 bit PWM for all other cpu types
/* Defines the maximum number of supported pwm channels. This is restriced by the PCA9685 controller */
#define PWM_CHANNELS 4
#define PWM_CHANNEL_0 FUNC_GPIO0
#define PWM_CHANNEL_1 FUNC_GPIO1
#define PWM_CHANNEL_2 FUNC_GPIO2
#define PWM_CHANNEL_3 FUNC_GPIO3
#endif // defined(__AVR__)

typedef struct
{
	String Key;
	String Value;
} Option;

#if defined(ESP8266)
enum WlanMode
{
	WlanModeClient,
	WlanModeAccessPoint
};

typedef struct
{
	WlanMode Mode;
	String SSID;
	String PW;
	bool ManualIP;
	IPAddress IP;
	IPAddress Gateway;
} WlanConfig;
#endif

/*This struct defines a target value at a specific time */
typedef struct
{
	uint8_t Value; // Percentage value must between 0 and 100
	time_t Time;   // The time in seconds after 01.01.1970 when the value should be reached.
} Target;

#if defined(USE_WEBSERVER)
/* Macro state tracking for temporary lighting overrides */
typedef struct
{
	bool active;														// Is a macro currently running?
	time_t startTime;													// Unix timestamp when macro was activated
	uint32_t duration;													// Macro duration in seconds
	char macroId[20];													// Macro identifier (e.g., "macro_001")
	Target originalTargets[PWM_CHANNELS][MAX_TARGET_COUNT_PER_CHANNEL]; // Backup of original schedules
	uint8_t originalTargetCounts[PWM_CHANNELS];							// Backup of original target counts
} MacroState;
#endif

class PwmChannel
{
private:
	int16_t _PwmTarget = 0;
	int16_t _PwmValue = 1;

public:
	// Allow the debug endpoint to report live PWM state without guessing.
	friend void handleApiDebug();
	uint8_t ChannelAddress; // Contains the address or pin for setting the pwm value
	Target Targets[MAX_TARGET_COUNT_PER_CHANNEL];
	uint8_t TargetCount;
	uint16_t CurrentWriteValue;
	bool HasToWritePwm; // Indecates, that a new pwm values has to be written to the pwm device
	bool TestMode;
	time_t TestModeSetTime;
	uint8_t TestValue;
	time_t CurrentSecOfDay;
	time_t CurrentMilli;

	PwmChannel()
	{
		TestMode = false;
	}

	uint8_t addTarget(Target t); // Inserts a new target (time and value for the channel) and gives back the position.

	bool removeTargetAt(uint8_t pos); // Removes the target at the specified position

	void proceedCycle(time_t currentSecOfDay, time_t currentMilliOfSec); // the main function for each step. Here the pwm value will be calculated
};

#if defined(USE_DS18B20_TEMP_SENSOR)

class TemperatureReader
{
public:
	OneWire temp = OneWire(DS18B20_PIN);
	bool Status = false;
	byte temp_addr[8];
	byte temp_data[12];
	byte temp_type_s;
	// Stores the current temperature
	float _TemperatureInCelsius;
	byte temp_present = 0;
	// This is used in the temperature read funktion. To read a temperature value from the sensor takes at least one second.
	// But we can not wait for, because the cycle time in AquaControl has to be as low as possible. Thats why we will use a ticktock princip.
	// To  read a temperatur value we have to call the temp read function twice. The first call prepares the sensor. The second call reads the value.
	// Between the calls at least one second has to leave.
	bool _TickTock = false;
	time_t _NextPossibleActivity;
	uint8_t _UpdateIntervall = 10;

	// Reads the temperature from the DS18B20 sensor and stores it to the member. The function decides by it self, if a temperatur value will we red.
	// So, do not think, that a call of the function will update the _TemperatureInCelcius member for shure.
	// The function returns true, if the temperature value was updated
	bool readTemperature(time_t currentSeconds);
	bool init(time_t currentSecOfDay);
};

#endif

// Time sync source tracking for hybrid time sync implementation
enum class TimeSyncSource
{
	Unknown, // Not yet synced or sync failed
	Ntp,	 // Time synced from NTP server
	Rtc,	 // Time synced from DS3231 RTC
	Api		 // Time manually set via /api/time/set
};

class AquaControl
{
public:
	time_t CurrentSecOfDay;
	time_t CurrentMilli;

#if defined(USE_PCA9685)
	Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();
#endif

#if defined(USE_DS18B20_TEMP_SENSOR)
	TemperatureReader _Temperature;
	uint8_t _TemperatureUpdateIntervall = 10; // Update the temperatur every 10 sec
#endif

#if defined(ESP8266)
	// Initializes the Wifi-Network
	void initESP8266NetworkConnection();
	// Read ant write the Wlan configuration
	bool readWlanConfig();
	bool writeWlanConfig();
	// Read and write led configuration
	bool readLedConfig();
	bool writeLedConfig(uint8_t pwmChannel);
	// Helper: Write targets to file with given path (reusable for schedules and macros)
	bool writeTargetsToFile(const String &pathPrefix, uint8_t channel, PwmChannel &pwmChannel);
#endif

	// Initializes the time synch mechanisim (RTC or NTP)
	void initTimeKeeper();

	uint8_t getPhysicalChannelAddress(uint8_t channelNumber);

	PwmChannel _PwmChannels[PWM_CHANNELS]; // Stores the PWM chanels
	bool _IsFirstCycle;				   // Indicates, that we have not set any pwm value
private:
	// Issue #7: single monotonic time base. The TimeLib second (RTC-anchored)
	// and millis()%1000 wrap at different phases, producing a ~1 Hz sawtooth
	// in the fade interpolation. We therefore re-anchor the millisecond phase
	// exactly when the second changes, so secOfDay*1000+milliOfSec is monotonic.
	time_t _lastSod = -1;
	uint32_t _sodEdgeMilli = 0;
public:
#if defined(ESP8266)
	WlanConfig _WlanConfig;

	// Debug issue #26: WiFi connection history ring buffer. Records state
	// changes with time-of-day so "was the device reachable at H:MM" can be
	// answered after the fact. Recording only - no supervision/reconnect
	// behavior change lives in this branch (that is issue #9 work).
	static constexpr uint8_t WIFI_HISTORY_SIZE = 8;
	struct WifiEvent
	{
		char event[16];  // "connected" | "disconnected" | "boot-connect-failed"
		uint8_t reason;  // disconnect reason code (0 for non-disconnect events)
		time_t ts;       // seconds of day when it happened
	};
	WifiEvent _wifiHistory[WIFI_HISTORY_SIZE] = {};
	uint8_t _wifiHistoryCount = 0;
	uint8_t _wifiHistoryPos = 0; // next write slot (ring)

	void recordWifiEvent(const char *event, uint8_t reason)
	{
		WifiEvent &e = _wifiHistory[_wifiHistoryPos];
		strncpy(e.event, event, sizeof(e.event) - 1);
		e.event[sizeof(e.event) - 1] = '\0';
		e.reason = reason;
		e.ts = elapsedSecsToday(now());

		_wifiHistoryPos = (_wifiHistoryPos + 1) % WIFI_HISTORY_SIZE;
		if (_wifiHistoryCount < WIFI_HISTORY_SIZE)
			_wifiHistoryCount++;

		char buf[64];
		sprintf(buf, "%02u:%02u:%02u WiFi %s (reason %u)",
				(unsigned)hour(e.ts), (unsigned)minute(e.ts), (unsigned)second(e.ts),
				event, (unsigned)reason);
		Serial.println(buf);

		// Issue #28: WiFi state changes also go to the persistent SD event log.
		logEvent(buf);
	}
#endif

#if defined(ESP8266)
	// Issue #28: persistent event log on the SD card (log/events.log).
	// Answers "what happened while nobody was watching": the network dropout
	// incidents of 2026-09-24/25 could not be explained afterwards because the
	// serial buffer dies together with reachability. Recording only.
	static constexpr const char *LOG_DIR = "log";
	static constexpr const char *LOG_PATH = "log/events.log";
	static constexpr uint32_t LOG_ROTATE_BYTES = 500UL * 1024UL;

	uint32_t _lastHeartbeatLogMs = 0; // last heartbeat millis (pacing)
	uint16_t _logLineCount = 0;		 // lines since last rotation check
	bool _sdLogOk = false;			 // set at boot, cleared on first failed write

	void logEvent(const char *line)
	{
		if (!_sdLogOk)
			return;
		if (++_logLineCount >= 500)
		{
			rotateIfNeeded();
			_logLineCount = 0;
		}
		File f = SD.open(LOG_PATH, FILE_WRITE);
		if (!f)
		{
			_sdLogOk = false; // one warning per boot, then silent
			Serial.println(F("WARN: SD event log write failed - logging disabled this boot"));
			return;
		}
		f.print(line);
		if (line[strlen(line) - 1] != '\n')
			f.print('\n');
		f.close();
	}

	void rotateIfNeeded()
	{
		File f = SD.open(LOG_PATH);
		if (!f)
			return;
		uint32_t size = f.size();
		f.close();
		if (size < LOG_ROTATE_BYTES)
			return;
		char oldPath[24];
		strcpy(oldPath, LOG_PATH);
		strcat(oldPath, ".1");
		if (SD.exists(oldPath))
			SD.remove(oldPath);
		SD.rename(LOG_PATH, oldPath); // keep one generation only
	}

	// Called once right after SD.begin() in init(), BEFORE network init, so
	// even the boot connect result lands in the log.
	void initEventLog()
	{
		_sdLogOk = true;

		// log/ directory: SD lib has no mkdir in some cores - tolerate failure.
		if (!SD.mkdir(LOG_DIR))
		{
			File d = SD.open(LOG_DIR);
			_sdLogOk = d && d.isDirectory();
			if (d)
				d.close();
		}
		if (!_sdLogOk)
		{
			Serial.println(F("WARN: event log disabled (no log/ directory on SD)"));
			return;
		}

		rotateIfNeeded();

		// A power pull during a write leaves one truncated last line. Detect it
		// and record the gap so the log stays line-parseable.
		File r = SD.open(LOG_PATH);
		if (r && r.size() > 0)
		{
			uint32_t size = r.size();
			r.seek(size - 1);
			bool truncatedTail = (r.read() != '\n');
			r.close();
			if (truncatedTail)
			{
				File a = SD.open(LOG_PATH, FILE_WRITE);
				if (a)
				{
					a.print(F("<line truncated: previous run ended mid-write>\n"));
					a.close();
				}
			}
		}

		// THE discriminator: why did we reboot? (brownout / WDT / clean)
		char buf[96];
#if defined(ESP8266)
		// Esp::getResetReason() returns a translated string from the SDK
		// ("Software/System restart", "Boot log", etc.) - log it verbatim.
		String rr = ESP.getResetReason();
		snprintf(buf, sizeof(buf), "boot (reset reason: %s)", rr.c_str());
#else
		sprintf(buf, "boot (reset reason: n/a)");
#endif
		logEvent(buf);
		Serial.println(buf);
	}

	// Heartbeat from the main loop: proves the device was alive and lets the
	// next boot measure an outage gap. One write per 5 min, never in an ISR.
	void logHeartbeat()
	{
		if (!_sdLogOk)
			return;
		uint32_t ms = millis();
		if (_lastHeartbeatLogMs != 0 && ms - _lastHeartbeatLogMs < 5UL * 60UL * 1000UL)
			return;
		_lastHeartbeatLogMs = ms;
		char buf[48];
		sprintf(buf, "%02u:%02u:%02u heartbeat up=%lus",
				(unsigned)hour(), (unsigned)minute(), (unsigned)second(),
				(unsigned long)(ms / 1000));
		logEvent(buf);
	}

	// Current byte size of the event log (0 if unavailable).
	uint32_t eventLogSize()
	{
		if (!_sdLogOk)
			return 0;
		File f = SD.open(LOG_PATH);
		if (!f)
			return 0;
		uint32_t size = f.size();
		f.close();
		return size;
	}
#endif
#if defined(USE_WEBSERVER)
	MacroState _activeMacro; // Current active macro state
#endif

	// Time sync state tracking
	time_t _LastTimeSync;				// Timestamp of last successful sync
	TimeSyncSource _LastTimeSyncSource; // Source of last successful sync
	bool _NtpSyncFailed;				// True if last NTP attempt failed (signals browser to auto-sync)

	AquaControl()
	{
		_IsFirstCycle = true;
#if defined(USE_WEBSERVER)
		_activeMacro.active = false;
		_activeMacro.startTime = 0;
		_activeMacro.duration = 0;
		_activeMacro.macroId[0] = '\0';
#endif
		_LastTimeSync = 0;
		_LastTimeSyncSource = TimeSyncSource::Unknown;
		_NtpSyncFailed = false;
	}

	void init();

	bool addChannelTarget(uint8_t channel, Target target);

	void proceedCycle();

	void writePwmToDevice(uint8_t channel);

#if defined(USE_WEBSERVER)
	/* Macro activation and management */
	bool activateMacro(const String &macroId, uint32_t duration);
	void restoreSchedule();
	bool isMacroActive() const { return _activeMacro.active; }
	uint32_t getMacroTimeRemaining() const;
#endif

#if defined(ESP8266)
	IPAddress extractIPAddress(const String &sIP);
#endif
};

#endif // #ifndef __AQUACONTROL_H_
