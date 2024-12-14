from flask import Flask, request, jsonify
import common.http_wrapper as http_wrapper
import json
from typing import Any

app = Flask(__name__)
with open('config.json') as config_file:
    config = json.load(config_file)

WAKE_ON_LAN_API_URL = "https://services.wakeonlan"


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
async def proxy(path):

    host = request.headers.get("Host")
    host_config = config.get(host)

    if (not await handle_machine_state(host_config)):
        return jsonify("error", "Failed to activate service"), 502

    post_data = None
    if (request.method == 'POST'):
        try:
            post_data = request.get_json()
        except:
            post_data = {}

    target_app_url = f"{host_config.get('address')}:{host_config.get('port')}"
    response = await http_wrapper.send_request(
        url=f"{target_app_url}/{path}",
        request_type=request.method,
        headers=request.headers,
        query=request.args,
        post_data=post_data
    )

    print(f"Response from {target_app_url}/{path}: {response}")

    return jsonify(response.body), response.status


async def handle_machine_state(host_config: Any) -> bool:
    print(f"Host config is {host_config}")
    if (await is_app_running(host_config.get('address'))):
        return True
    else:
        return await wake_machine(host_config)


async def is_app_running(app_url: str) -> bool:
    request_path = f"{app_url}/"
    print(f"Checking if app is running at {request_path}")
    response = await http_wrapper.send_request(request_path, "GET", {})
    return response.status == 200


async def wake_machine(host_config: Any) -> bool:
    post_data = {
        "mac_address": host_config.get("mac_address"),
        "ip_address": host_config.get("address"),
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "/",
        "Connection": "keep-alive",
    }
    request_url = f"{WAKE_ON_LAN_API_URL}/wake"
    print(f"Waking machine at {request_url}")
    response = await http_wrapper.send_request(request_url, "POST", headers, None, post_data)
    if (response.status != 200):
        print(f"Failed to wake machine: {response.status} trying again")
        response = await http_wrapper.send_request(request_url, "POST", headers, None, post_data)
        print(f"Second attempt response: {response}")
    return response.status == 200 and response.body["exit_code"] == 0


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
