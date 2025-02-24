import os
import zmq
import base64
import sys
from werkzeug.utils import secure_filename
from dotenv import dotenv_values

BASE_DIR = "uploads"

config = dotenv_values(".env")

if config.get('CONTAINERIZED') == 'False':
    mapping = config['STANDALONE_MAPPING']
else:
    mapping = config['SERVER_CONTAINER_MAPPING']


def path_verification(campaign_name, file_name=None):
    sec_file_name = ''
    sec_campaign = secure_filename(campaign_name)
    path = os.path.join(BASE_DIR, sec_campaign)

    if file_name is not None:
        sec_file_name = secure_filename(file_name)
        path = os.path.join(path, sec_file_name)

    return path


def upload(request):
    path = None
    campaign_name = request["campaign"]
    file_name = request["file_name"]

    try:
        path = path_verification(campaign_name)
        os.makedirs(path, exist_ok=True)
        path = path_verification(campaign_name, file_name)
        path = os.path.join(path)

        data = socket.recv()
        data = base64.b64decode(data)

        with open(path, "wb") as f:
            f.write(data)
    except Exception as e:
        print('Exception Thrown', e)
        return {
            "Status": "Failure",
            "Message": f"<{file_name}> failed to upload to <{path}>"
        }

    finally:
        return {"Status": "Success",
                "Message": f"<{file_name}> uploaded to <{path}>."}


def download(request):
    campaign_name = request["campaign"]
    file_name = request["file_name"]

    path = path_verification(campaign_name, file_name)
    path = os.path.join(path)

    if not os.path.exists(path):
        return {"Status": " Failure",
                "Message": "File not found."}

    with open(path, "rb") as f:
        file_content = f.read()

    encoded_data = base64.b64encode(file_content)
    response_meta = {
        "Status": "Success",
        "Message": f"Downloaded <{file_name}> from <{path}>",
    }

    socket.send_json(response_meta, zmq.SNDMORE)
    socket.send(encoded_data)
    return None


def get_list(request):
    campaign_name = request["campaign"]
    path = path_verification(campaign_name)
    path = os.path.join(path)

    if not os.path.exists(path):
        return {
            "Status": "Failure",
            "Message": f"The directory <{campaign_name}> does not exist."
        }

    files = os.listdir(path)
    return {
        "Status": "Success",
        "Files": files,
        "Message": f"Found <{len(files)}> file(s) in <{campaign_name}>."
    }


def request_handler(request):
    print("Request received:")
    for key in request.keys():
        print(f"{key}: {request[key]}")
    command = request.get("command")
    if command == "upload":
        return upload(request)
    elif command == "download":
        return download(request)
    elif command == "list":
        return get_list(request)
    else:
        data = socket.recv(zmq.NOBLOCK)
        data = base64.b64decode(data)
        print(f'Flushed {sys.getsizeof(data)} bytes from socket')
        return {"Status": "Failure",
                "Message": f"<{command}> is an invalid command."}


if __name__ == "__main__":
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"{mapping}")

    print(f"Listening on {mapping}")
    os.makedirs(BASE_DIR, exist_ok=True)

    while True:
        request_json = socket.recv_json()
        response = request_handler(request_json)

        if response is not None:
            print(f"Sending response: {response}")
            socket.send_json(response)

