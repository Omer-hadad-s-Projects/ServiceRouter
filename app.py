from flask import Flask, request, Response, jsonify
import common.http_wrapper as http_wrapper
import json

app = Flask(__name__)
with open('config.json') as config_file:
    config = json.load(config_file)


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
async def proxy(path):

    host = request.headers.get("Host")
    host_config = config.get(host)
    target_app_url = f"{host_config.get('dns')}:{host_config.get('port')}"

    is_running = await is_app_running(target_app_url)
    if (not is_running):
        return jsonify("error", "Target application is not running"), 500

    post_data = None
    if (request.method == 'POST'):
        try:
            post_data = request.get_json()
        except Exception as e:
            post_data = {}

    response = await http_wrapper.send_request(
        url=f"{target_app_url}/{path}",
        request_type=request.method,
        headers=request.headers,
        query=request.args,
        post_data=post_data
    )

    print(f"Response from {target_app_url}/{path}: {response}")

    return jsonify(response.body), response.status


async def is_app_running(app_url):
    request_path = f"{app_url}/"
    print(f"Checking if app is running at {request_path}")
    response = await http_wrapper.send_request(request_path, "GET", {})
    return response.status == 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
