import json

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


### Flask ###
app = Flask(__name__)


@app.route("/", methods=['POST', 'GET'])

def index():

    if request.method == 'POST':

        # Get the POST data sent from Meraki
        meraki_post = request.json
        print("\n")

        if meraki_post['secret'] == get_env_var("meraki_secret"):

            output = json.dumps(meraki_post, indent=4)
            print(output)

    elif request.method == "GET":

        print(request.headers)

        return get_env_var("meraki_secret2")

    return request.method


# Run the server app
if __name__ == "__main__":
    # Do not keep debug=True in production

    context=('live-demo22_online.chained.crt', 'private90trial.key')
    app.run(host='0.0.0.0', port=5014, use_reloader=True, debug=True, threaded=True, ssl_context=context) #, ssl_context='adhoc')
