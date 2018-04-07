# pycame
Python script to interact with Came domotique system.

Can be used for home automation with a simple crontab.

Features:
* Lights: turn on, turn off, set dimmer intensity
* Blinds: open, close, set an angle
* Heating: turn off, set specific temperature, turn on automatic mode, turn on jolly mode
* Scenarios: activate scenarios pre-programmed in domotique server


# Quick-start

- [ ] Update `settings.json`.
- [ ] Run `./domo.py layout` to initialize `layout.json`.
- [ ] Close blinds in kitchen with `./domo.py blinds kitchen close`.
- [ ] Turn on lights in the hallway with `./domo.py lights hall open`.
- [ ] Turn on heating and set temperature to 18 degrees Celsia with `./domo.py thermo man 180`.
- [ ] Read current temperature with `./domo.py get temp`.
- [ ] Show available commands with `./domo.py`.


# Configuration

## Main settings
The main configuration is read from the file `settings.json`, residing
in the same directory as the script `domo.py`.
This can be changed by modify the variable `settings_filename` in `domo.py`.

You must configure the URL of the domotique server and login credentials.
The sample config file includes default login credentials.

## Layout
The layout (mapping from names to IDs used by domotique system) is
stored in the file `layout.json`.

The first time you use the script, you must initialize the file
`layout.json` with `./domo.py layout`. It retrieves the names and IDs
of lights, blinds, and scenarios from the domotique server.

The names used by the domotique system do not seem to be end-user modifiable.
However, you can provide your own names (used as cmd line arguments)
to override the names setup in the domotique server. The mapping of
names is configured in the file `settings.json` under `layout_names`.

The command `./domo.py layout` should also be used when the domotique
server was re-programmed and the IDs changed.


# Network protocol

The domotique server offers communication in the form of
JSON-formatted messages exchanged over unencrypted HTTP.

The client must login with username and password to obtain a session
ID, called `client_id`. Subsequent requests must include the session
ID.

The session ID expires if no messages are exchanged for some time
(several minutes?). For furter communication, the client must re-login
to obtain a new session ID.

The session ID should be reused instead of logging in and obtaining a
new session ID for each request. The reason is that the domotique
server supports a few tens of concurrent sessions. If this limit is
reached than no new logins are possible until active session IDs time
out. To this end, the python script `domo.py` stores the session ID in
a local file.


# Security

A possible way to secure the domotique system is to misconfigure the
network settings of the domotique server and use an invalid default
gateway. That way, the domotique system cannot directly communicate
with the Internet and unencrypted communication is only possible
within the local network.

Interaction over the Internet is only possible via another server in
the local network, such a Raspberry Pi, offering secure protocols like
SSH.