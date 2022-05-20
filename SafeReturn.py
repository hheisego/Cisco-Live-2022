import requests
import json
from webexteamssdk import WebexTeamsAPI
from flask import Flask, request

with open("secrets.json") as f:
    configs = json.loads(f.read())

def get_env_var(setting, configs=configs):
    try:
        val = configs[setting]
        if val == "True":
            val = True
        elif val == "False":
            val = False
        return val

    except KeyError:

        raise NotImplementedError("secrets.json is missing")

class CiscoLive:

    def send_message(self, msg):

        mails = ['hemorale@cisco.com', 'hheisego@cisco.com']

        for i in mails:

            live_bot.messages.create(toPersonEmail=i, text=msg)


    def get_co2(self):

        url = "https://api.growflux.com"

        payload = {}
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + get_env_var("co2_token")
        }

        # get all APs
        resource = "/v1/aps"
        response = requests.request("GET", url + resource, headers=headers, data=payload)
        response_parsed = json.loads(response.text)
        aps = response_parsed["message"]["aps"]

        co2_levels = ''
        co2_alarm = 0
        for ap in aps:

            # get all CO2 sensors per AP
            resource = "/v1/ap/" + ap["id"] + "/co2_sensors"
            response = requests.request("GET", url + resource, headers=headers, data=payload)
            response_parsed = json.loads(response.text)

            co2_sensors = response_parsed["message"]["co2_sensors"]
            print(co2_sensors)
            # for each sensor, print out its values
            for sensor in co2_sensors:
                co2_levels += "\nTimestamp: " + str(co2_sensors[sensor]["metrics"]["data"]["timestamp"])
                co2_levels += "\nCO2 levels: " + str(co2_sensors[sensor]["metrics"]["data"]["C_co2"])
                co2_levels += "\nTemperature: " + str(co2_sensors[sensor]["metrics"]["data"]["C_t"])
                co2_levels += "\nHumidity: " + str(co2_sensors[sensor]["metrics"]["data"]["C_rh"])
                co2_levels += "\nVoltage: " + str(co2_sensors[sensor]["metrics"]["data"]["C_v"])
                co2_levels += "\nPressure: " + str(co2_sensors[sensor]["metrics"]["data"]["C_p"])

                co2_alarm = co2_sensors[sensor]["metrics"]["data"]["C_co2"]
                print("Timestamp: " + str(co2_sensors[sensor]["metrics"]["data"]["timestamp"]))
                print("CO2 levels: " + str(co2_sensors[sensor]["metrics"]["data"]["C_co2"]))
                print("Temperature: " + str(co2_sensors[sensor]["metrics"]["data"]["C_t"]))
                print("Humidity: " + str(co2_sensors[sensor]["metrics"]["data"]["C_rh"]))
                print("Voltage: " + str(co2_sensors[sensor]["metrics"]["data"]["C_v"]))
                print("Pressure: " + str(co2_sensors[sensor]["metrics"]["data"]["C_p"]))

        return co2_levels, co2_alarm


    def meraki_data(self, meraki_post):

        co2_levels, co2 = self.get_co2()
        ap_connected = ''
        nearby = ''
        ssid = ''
        room_count = 0

        if meraki_post['type'] == 'WiFi':

            for i in meraki_post['data'].get('observations'):

                manufacture = str(i.get('manufacturer'))

                if i.get('ssid') is not None:

                    ssid = str(i.get('ssid'))

                if i.get('ssid') is not None and i['latestRecord'].get('nearestApRssi') >= -61:

                    ap_connected += "\nDevice mac: " + i.get('clientMac') +"\nRSSI: " + str(i['latestRecord'].get('nearestApRssi'))
                    room_count += 1


                elif i.get('ssid') is None and i['latestRecord'].get('nearestApRssi') >= -55 and manufacture != 'Meraki':

                    nearby += "\nDevice mac: " + i.get('clientMac') + "\nRSSI: " + str(i['latestRecord'].get('nearestApRssi'))
                    room_count += 1

            if co2 >= 800 and room_count > 0:

                msg = ssid + str(ap_connected) + '\n' + str(nearby)
                msg += "\nCO2: " + str(co2) + " | Devices count: " + str(room_count) + "  -- > Sal Corriendo\n" + co2_levels
                self.send_message(msg)

            elif co2 < 800 and room_count > 0:

                msg = str(ap_connected) + '\n' + str(nearby)
                msg += " CO2: " + str(co2) + " | Devices count: " + str(room_count) + "\n" + co2_levels
                self.send_message(msg)

        return {"status": 200}


#Instances
### Webex ###
live_bot = WebexTeamsAPI(access_token=get_env_var("BOTOKEN"))

### Flask ###
app = Flask(__name__)

# Cisco Live
cisco_live = CiscoLive()


@app.route("/", methods=['POST', 'GET'])

def index():

    if request.method == 'POST':

        # Get the POST data sent from Meraki
        meraki_post = request.json
        print("\n")
        print(type(meraki_post), meraki_post)
        print("\n")

        if meraki_post['secret'] == get_env_var("meraki_secret"):

            cisco_live.meraki_data(meraki_post)

    elif request.method == "GET":

        print(request.headers)

        return get_env_var("meraki_secret2")

    return request.method


# Run the server app
if __name__ == "__main__":
    # Do not keep debug=True in production
    #context = ('/etc/pki/tls/certs/r2s21/ready2solve2021.crt', '/etc/pki/tls/certs/r2s21/Private.key')
    context=('live-demo22_online.chained.crt', 'private90trial.key')
    app.run(host='0.0.0.0', port=5013, use_reloader=True, debug=True, threaded=True, ssl_context=context) #, ssl_context='adhoc')
