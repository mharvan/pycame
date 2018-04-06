#!/usr/bin/python3
#
# Library for domotique system CAME.
#
# Implements commands to control blinds (volets), lights, and thermoregulation settings.
#
# Keeps session information (client_id retrieved after login) in a
# local file in order to re-use the existing session. This is to
# minimize the number of open sessions as the domotique system can
# only deal with a rather small number of concurrently open sessions.
#
# When called as main program, it includes a command parser (cmd line
# arguments). Example commands:
#     python3 domo.py blinds kitchen angle 1
#     python3 domo.py blinds bedroom angle 0.2
#     python3 domo.py blinds bedroom down
#     python3 domo.py blinds streck up
#     python3 domo.py lights sam on
#     python3 domo.py lights sam dim 60
#     python3 domo.py lights living dim 60
#     python3 domo.py lights terasse off
#     python3 domo.py thermo off
#     python3 domo.py thermo auto
#     python3 domo.py thermo man 240
#     python3 domo.py thermo jolly
#     python3 domo.py scenario lights_off
#     python3 domo.py scenario lights_on
#     python3 domo.py scenario blinds_down
#     python3 domo.py scenario blinds_up
#     python3 domo.py status
#
# Example crontab:
# 50 05 * * * python3 /home/mharvan/pycame/domo.py blinds kitchen angle 1
# 50 06 * * * python3 /home/mharvan/pycame/domo.py blinds bedroom angle 0.2
# 55 08 * * * python3 /home/mharvan/pycame/domo.py blinds bedroom down
# 55 08 * 05-09 * python3 /home/mharvan/pycame/domo.py blinds streck down
# 20 13 * 05-09 * python3 /home/mharvan/pycame/domo.py blinds kitchen angle 0.35
#
#
# TODO:
# * Determine control IDs (mapping from human-freindly names to act_id)
#   from server instead of hard-coding them
# * interactive usage - read in commands from stdin
# * motion sensor notifications
# * temperature sensor readings
# * keepalive
#
# * logout
#   Check traffic when changing accounts.
#

import json
import requests
import sys
import time

# Settings
url = "http://192.168.0.3/domo/"
sl_login = "admin"
sl_pwd = "admin"
client_id_filename = "/tmp/.client_id"
settings_filename = "settings.json"

# Global variables (state)
client_id = ""
cseq = 0
layout = {}
settings = {}


# Print to STDERR
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# Initialization
def init():
    global settings
    global url
    global sl_login
    global sl_pwd
    global client_id_filename
    # Read in settings from file
    try:
        with open(settings_filename, 'r') as infile:
            settings = json.load(infile)
        url = settings["url"]
        sl_login = settings["sl_login"]
        sl_pwd = settings["sl_pwd"]
        client_id_filename = settings["client_id_filename"]
    except IOError:
        eprint("Could not read settings file:", settings_filename)
        sys.exit(1)
    except KeyError:
        eprint("Mandatory settings missing.")
        sys.exit(1)

    global client_id
    # Read in client_id from file
    try:
        with open(client_id_filename, 'rt') as infile:
            client_id = infile.read()
    except IOError:
        eprint("Could not read client_id file:", client_id_filename)
        eprint("Will re-login.")

    global layout
    # Read in layout from file
    try:
        with open(settings["layout_filename"], 'r') as infile:
            layout = json.load(infile)
    except IOError:
        eprint("Could not read layout file:", settings["layout_filename"])
        eprint("Please initialize it with the option layout.")


# Send login request.
def login():
    global cseq
    global client_id
    cmd = {
        "sl_cmd": "sl_registration_req",
        "sl_login": sl_login,
        "sl_pwd": sl_pwd
    }
    data = {"command": json.dumps(cmd, indent=4)}
    #print(data)
    resp = requests.post(url, data=data)

    # Extract client_id from login response.
    #print('status: ', resp.status_code)
#    print('txt: ', resp.text)
    #print('json: ', resp.json())
    client_id = resp.json()['sl_client_id']
    cseq = 0

    # Write client_id to file
    try:
        f = open(client_id_filename, 'wt')
        f.write(client_id)
    except IOError:
        print("Could not write file:", client_id_filename)

def gen_cmd(appl_msg):
    global cseq
    cseq += 1

    appl_msg["client"] = client_id
    appl_msg["cseq"] = cseq

    cmd={
        "sl_appl_msg": appl_msg,
        "sl_appl_msg_type": "domo",
        "sl_client_id": client_id,
        "sl_cmd": "sl_data_req"
    }
        
    data = {"command": json.dumps(cmd, indent=4)}
    #print(data)
    resp = requests.post(url, data=data)

    #print('status: ', resp.status_code)
    #print('json: ', resp.json())

    if (resp.status_code == 200):
        if resp.json()["sl_data_ack_reason"] == 0:
            # print("Command OK.")
            pass
        elif resp.json()["sl_data_ack_reason"] == 8:
            print("Must login again.")
            login()
            gen_cmd(appl_msg)
        else:
            print("Unknown ack reason")
            print("resp:", resp.json())
        return resp.json()
    else:
        print("Unexpected status code", resp.status_code)
        print("resp:", resp.text)
        
def cmd_name(name):
    global cseq
    cseq += 1

    appl_msg = {
        "client": client_id,
        "cseq": cseq,
        "cmd_name": name
    }
    cmd={
        "sl_appl_msg": appl_msg,
        "sl_appl_msg_type": "domo",
        "sl_client_id": client_id,
        "sl_cmd": "sl_data_req"
    }
        
    data = {"command": json.dumps(cmd, indent=4)}
    #print(data)
    resp = requests.post(url, data=data)

    #print('status: ', resp.status_code)
    #print('json: ', json.dumps(resp.json(), indent=4))

    if (resp.status_code == 200):
        if resp.json()["sl_data_ack_reason"] == 0:
            # print("Command OK.")
            return resp.json()
            #pass
        elif resp.json()["sl_data_ack_reason"] == 8:
            print("Must login again.")
            login()
            gen_cmd(appl_msg)
        else:
            print("Unknown ack reason")
            print("resp:", resp.json())
        return resp.json()
    else:
        print("Unexpected status code", resp.status_code)
        print("resp:", resp.text)

def get_thermo():
    global cseq
    cseq += 1

    appl_msg = {
        "client": client_id,
        "cseq": cseq,
        "cmd_name": "nested_thermo_list_req",
        "extended_infos": 2,
        "topologic_scope": "plant",
        "value": 0
    }
    cmd={
        "sl_appl_msg": appl_msg,
        "sl_appl_msg_type": "domo",
        "sl_client_id": client_id,
        "sl_cmd": "sl_data_req"
    }
        
    data = {"command": json.dumps(cmd, indent=4)}
    #print(data)
    resp = requests.post(url, data=data)
    #print('status: ', resp.status_code)
    #print('json: ', json.dumps(resp.json(), indent=4))
    return resp.json()

def get_lights():
    global cseq
    cseq += 1

    appl_msg = {
        "client": client_id,
        "cseq": cseq,
        "cmd_name": "nested_light_list_req",
        "topologic_scope": "plant",
        "value": 0
    }
    cmd={
        "sl_appl_msg": appl_msg,
        "sl_appl_msg_type": "domo",
        "sl_client_id": client_id,
        "sl_cmd": "sl_data_req"
    }
        
    data = {"command": json.dumps(cmd, indent=4)}
    #print(data)
    resp = requests.post(url, data=data)
    #print('status: ', resp.status_code)
    #print('json: ', json.dumps(resp.json(), indent=4))
    return resp.json()

def get_layout():
    global layout

    layout = {}
    # Get list of features
    features = cmd_name("feature_list_req")["list"]
    print("Features:")
    for feature in features:
        print("\t" + feature)

    # Get details for supported features
    if "scenarios" in features:
        feature="scenarios"
        layout[feature] = {}
        print("Requesting list of {}".format(feature))
        resp = cmd_name("{}_list_req".format(feature))
        #print('json: ' + json.dumps(resp, indent=4))
        for scenario in resp["array"]:
            #print("\tscenario: {}".format(scenario))
            # Name may be unicode.
            name = scenario["name"].encode(encoding="ascii", errors="ignore").decode("ascii")
            act_id = scenario["id"]
            try:
                layout_name = settings['layout_names'][feature][name]
            except:
                layout_name = name
            print("\t{} => {} => {}".format(name, layout_name, act_id))
            layout[feature][layout_name] = act_id

    if "openings" in features:
        feature="blinds"
        layout[feature] = {}
        print("Requesting list of {}".format("openings"))
        resp = cmd_name("{}_list_req".format("openings"))
        #print('json: ' + json.dumps(resp, indent=4))
        for opening in resp["array"]:
            #print("\topening: {}".format(opening))
            # Name may be unicode.
            name = opening["name"].encode(encoding="ascii", errors="ignore").decode("ascii")
            open_act_id = opening["open_act_id"]
            close_act_id = opening["close_act_id"]
            try:
                layout_name = settings['layout_names'][feature][name]
            except:
                layout_name = name
            print("\t{} => {} => open {}, close {}".format(name, layout_name, 
                                                           open_act_id, close_act_id))
            layout[feature][layout_name] = open_act_id

    if "thermoregulation" in features:
        feature="thermoregulation"
        layout[feature] = {}
        print("Requesting thermoregulation list")
        resp = get_thermo()
        # act_id, temp
        #print('json: ' + json.dumps(resp, indent=4))
        act_id = resp["array"][0]["array"][0]["act_id"]
        temp = int(resp["array"][0]["array"][0]["temp"])
        print("\tact_id: {}".format(act_id))
        print("\ttemp: {}".format(temp))
        layout[feature] = act_id

    if "lights" in features:
        feature = "lights"
        layout[feature] = {}
        print("Requesting lights list")
        resp = get_lights()
        # act_id, temp
        #print('json: ' + json.dumps(resp, indent=4))
        for room in resp["array"][0]["array"]:
            #print("\troom: {}".format(room))
            for light in room["array"]:
                #print("\t\tlight: {}".format(light))
                # Name may be unicode.
                name = light["name"].encode(encoding="ascii", errors="ignore").decode("ascii")
                act_id = light["act_id"]
                try:
                    layout_name = settings['layout_names'][feature][name]
                except:
                    layout_name = name
                print("\t{} => {} => {}".format(name, layout_name, act_id))
                layout[feature][layout_name] = act_id

    # TODO: sicu
    #print('layout: ' + json.dumps(layout, indent=4))
    layout_filename = settings["layout_filename"]
    with open(layout_filename, 'w') as outfile:
        json.dump(layout, outfile, indent=4)
    print()
    print("Wrote layout to file", layout_filename)

# Modify thermoregulation settings.
#
# mode:
# 0 - off
# 1 - manual
# 2 - auto
# 3 - jolly
#
# temp: Temperature in degrees celsia, multiplied by 10.
#       E.g., 240 for 24 degrees celsia.
#
def thermo(mode=2, temp=240):
    act_id = layout['thermoregulation']
    appl_msg = {
        "act_id": act_id,
        "cmd_name": "thermo_zone_config_req",
        "extended_infos": 0,
        "mode": mode
    }

    if temp is not None:
        appl_msg["set_point"] = temp

    gen_cmd(appl_msg)

# Turn on/off lights and change dimmer setting.
#
# act_id
#  2 - Hall d'entree
#  3 - Lampe WC
#  4 - Lampe sejour
#  5 - Lampe s.a.m.
# 11 - Lampe chambre 1
# 16 - Lampe chambre 2
# 14 - Lampe sdbain
# 15 - Miroir sdbain
# 19 - Lampe vestiaire
# 20 - Lampe terrasse
# 
# wanted_status:
# 0 - off
# 1 - on
#
# perc: 0 - 100 percentage setting of the dimmer
#       Ignored for lights without dimmer.
#
def lights(act_id, wanted_status, perc=None):
    appl_msg = {
        "act_id": act_id,
        "cmd_name": "light_switch_req",
        "wanted_status": wanted_status
    }

    if perc is not None:
        appl_msg['perc'] = perc

    gen_cmd(appl_msg)


def set_dimmers(perc=60):
    lights(4, 1, perc)
    lights(5, 1, perc)
    

# Move window blinds (blinds) up and down.
# 
# "open_act_id":	7,
# "close_act_id":	8,
# "name":	"Volet sejour",

# "open_act_id":	9,
# "close_act_id":	10,
# "name":	"Volet cuisine",

# "open_act_id":	12,
# "close_act_id":	13,
# "name":	"Volet chambre 1",
# "open_act_id":	17,
# "close_act_id":	18,
# "name":	"Volet chambre 2",
#
#
# wanted_status:
# 0 - stop
# 1 - up
# 2 - down
def blinds(act_id, wanted_status):
    appl_msg = {
        "act_id": act_id,
        "cmd_name": "opening_move_req",
        "wanted_status": wanted_status
    }
    gen_cmd(appl_msg)

def blinds_angle(act_id, angle):
    # Move down for 1 sec to ensure closed angle
    blinds(act_id, 2)
    time.sleep(1)
    blinds(act_id, 0)
    # Wait a between commands
    time.sleep(1)
    # Move up to set new angle
    blinds(act_id, 1)
    time.sleep(angle)
    blinds(act_id, 0)
    # Safety fall-back: Unconditionally stop blinds movement.
    # Otherwise, the blinds would go fully up if last command did not get through.
    time.sleep(1)
    blinds(act_id, 0)

# Invoke a pre-defined scenario
#
# id:
# 1 - Lampes OFF
# 2 - Lampes ON",
# 3 - blinds close
# 4 - blinds open
def scenario(id):
    appl_msg = {
        "id": id,
        "cmd_name": "scenario_activation_req"
    }
    gen_cmd(appl_msg)

def status_update():
    appl_msg = {
        "cmd_name": "status_update_req"
    }
    resp = gen_cmd(appl_msg)
    results = resp['result']
    # print(json.dumps(results, indent=4))
    #print("type(results):", type(result))
    for result in results:
        #print("type(result):", type(i))
        if isinstance(result, dict):
            cmd_name = result["cmd_name"]
            print("cmd_name:", cmd_name)
            # if (cmd_name == "sicu_input_status_ind" or
            #     cmd_name == "sicu_central_status_ind"):
            if (cmd_name == "sicu_input_status_ind"):
                    status = result["status"]
                    name = result["name"]
                    print("=== %s %s %d === %s" %
                          (cmd_name, name, status, time.strftime('%a %H:%M:%S')))
            elif (cmd_name == "sicu_central_status_ind"):
                    status = result["status"]
                    name = result["name"]
                    print("=== %s %d === %s" %
                          (cmd_name, status, time.strftime('%a %H:%M:%S')))
            elif (cmd_name.startswith("sicu")):
                try:
                    status = result["status"]
                    print("=== %s %d === %s" % (cmd_name, status, time.strftime('%a %H:%M:%S')))
                    # if (status == 0 or status == 17):
                    #     print("=== No movement ===", time.strftime('%a %H:%M:%S'))
                    # else:
                    #     print("=== Movement ===", time.strftime('%a %H:%M:%S'))
                    # print("=== match ===")
                except KeyError:
                    print("No status in json.")
                print(json.dumps(result, indent=4))


def sicu_events():
    appl_msg = {
        "cmd_name": "sicu_events_list_req"
    }
    resp = gen_cmd(appl_msg)
    #results = resp['result']
    print(json.dumps(resp, indent=4))


def test_blinds_up_down():
    for act_id in [9, 10, 9, 10]:
        for status in [0, 1, 0, 2, 0]:
            print(act_id, status)
            blinds(act_id, status)
            time.sleep(10)

def test_blinds_angle():
    act_id = 9
    for angle in [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5, 0.6, 0.7, 0.8]:
        print(angle)
        blinds(act_id, 2)
        time.sleep(1)
        blinds(act_id, 0)
        time.sleep(0.3)
        blinds(act_id, 1)
        time.sleep(angle)
        blinds(act_id, 0)
        time.sleep(2)


def test():
    pass
    # # lights: Hall d'entre
    # lights(2,1)
    # time.sleep(3)
    # lights(2,0)
    # time.sleep(3)

    # # lights: Terrasse
    # lights(20,1)
    # time.sleep(5)
    # lights(20,0)

    # # lights: Living with dimmer
    # lights(4,1,20)
    # time.sleep(5)
    # lights(4,1,80)
    # time.sleep(5)
    # lights(4,1,60)
    # time.sleep(5)
    # lights(4,0)

    # # blinds: Cuisine
    # blinds(9,2)
    # time.sleep(2)
    # blinds(9,0)
    # time.sleep(3)
    # blinds(9,1)
    # time.sleep(0.5)
    # blinds(9,0)

    # # blinds: Bedroom
    # blinds(12,1)
    # time.sleep(0.7)
    # blinds(12,0)

    # 5:50
    # # blinds: Cuisine open
    # blinds(9,1)
    # time.sleep(1)
    # blinds(9,0)

    # 6:50
    # # blinds: Bedroom - wake up
    # blinds(12,1)
    # time.sleep(0.2)
    # blinds(12,0)

    # 8:55
    # # blinds: Bedroom close
    # blinds(12,2)

    # 8:55 (May - Sept)
    # # blinds: Streckraum close
    # blinds(17,2)

    # 14:00 (May - Sept)
    # # blinds: Cuisine close
    # blinds(9,2)
    # time.sleep(1)
    # blinds(9,0)

    # No movement for 2 hours: turn off all lights (scenario)

    # test_blinds_up_down()
    # test_blinds_angle()
    # test_blinds_angle()

    # set_dimmers()

def usage():
    supported_commands = ['blinds', 'lights', 'thermo', 'scenario',
                          'status', 'sicu_events']
    print("usage: domo.py command command_options")
    print("commands:", supported_commands)
    print("lights:", layout["lights"].keys())
    print("blinds:", layout["blinds"].keys())
    print("scenario:", layout["scenarios"].keys())

def parse_cmd(cmd):
    if (cmd[0] == 'blinds'):
        #act_id = volet_id[cmd[1]]
        act_id = layout["blinds"][cmd[1]]
        if (cmd[2] == 'stop'):
            status = 0
            blinds(act_id, status)
        elif (cmd[2] == 'up'):
            status = 1
            blinds(act_id, status)
        elif (cmd[2] == 'down'):
            status = 2
            blinds(act_id, status)
        elif (cmd[2] == 'angle'):
            angle = float(cmd[3])
            blinds_angle(act_id, angle)
        else:
            print("Command %s not understood." % cmd[2])
            print("Supported commands: stop, up, down, angle")
    elif (cmd[0] == 'lights'):
        #act_id = light_id[cmd[1]]
        act_id = layout["lights"][cmd[1]]
        print("act_id:", act_id)
        if (cmd[2] == 'off'):
            status = 0
            lights(act_id, status)
        elif (cmd[2] == 'on'):
            status = 1
            lights(act_id, status)
        elif (cmd[2] == 'dim'):
            status = 1
            perc = float(cmd[3])
            lights(act_id, status, perc)
        else:
            print("Command %s not understood." % cmd[2])
            print("Supported commands: off, on, dim")
    elif (cmd[0] == 'thermo'):
        if (cmd[1] == 'off'):
            mode = 0
            thermo(mode)
        elif (cmd[1] == 'man'):
            mode = 1
            temp = int(cmd[2])
            thermo(mode, temp)
        elif (cmd[1] == 'auto'):
            mode = 2
            thermo(mode)
        elif (cmd[1] == 'jolly'):
            mode = 3
            thermo(mode)
        else:
            print("Command %s not understood." % cmd[2])
            print("Supported commands: off, man, auto, joilly")
    elif (cmd[0] == 'status'):
        status_update()
    elif (cmd[0] == 'sicu_events'):
        sicu_events()
    elif (cmd[0] == 'scenario'):
        #id = scenario_id[cmd[1]]
        id = layout['scenarios'][cmd[1]]
        scenario(id)
    elif (cmd[0] == 'get'):
        if (cmd[1] == 'temp'):
            resp = get_thermo()
            temp = int(resp["array"][0]["array"][0]["temp"])
            print(temp)
        else:
            print("Command %s not understood." % cmd[2])
            print("Supported commands: temp")
    elif (cmd[0] == 'layout'):
        get_layout()
    else:
        print("Command %s not understood." % cmd[0])
        usage()

if __name__ == '__main__':
    init()
    parse_cmd(sys.argv[1:])
    # login()

    # 5:50
    # # blinds: Cuisine open
    # blinds(9,1)
    # time.sleep(1)
    # blinds(9,0)

    # 6:50
    # # blinds: Bedroom - wake up
    # blinds(12,1)
    # time.sleep(0.2)
    # blinds(12,0)

    # 8:55
    # # blinds: Bedroom close
    # blinds(12,2)

    # 8:55 (May - Sept)
    # # blinds: Streckraum close
    # blinds(17,2)

    # 14:00 (May - Sept)
    # # blinds: Cuisine close
    # blinds(9,2)
    # time.sleep(1)
    # blinds(9,0)

    # No movement for 2 hours: turn off all lights (scenario)
