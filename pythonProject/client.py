import os
import zmq
import base64
import re
import tkinter as tk
import banner
from tkinter import filedialog as fd
from dotenv import load_dotenv, dotenv_values


BASE_DIR = "downloads"
SUCCESS = "\033[92mSuccess\033[00m"
FAIL = "\033[91mFailure\033[00m"
FILES = f"Files"
CAMPAIGNS = f"Campaigns"
# ASCII escape sequences
BLINK = "\033[5m"
CYAN = "\033[96m"
GREEN = "\033[92m"
PURPLE = "\033[35m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[00m"

config = dotenv_values(".env")

if config.get('CONTAINERIZED') == 'False':
    mapping = config['STANDALONE_MAPPING']
else:
    mapping = config['CLIENT_CONTAINER_MAPPING']

regex = r"<([^>]*)>"


def selector():
    root = tk.Tk()
    root.withdraw()
    path = fd.askopenfilename()
    print(path)

    return path


def list_parser(categories, key):
    if categories is not None and len(categories) == 0:
        print(f"{key}:   {CYAN}{categories}{RESET}")
    elif categories is not None and len(categories) > 0:
        print(f"{key}:   {CYAN}{categories[0]}{RESET}")
        for i in range(1, len(categories)):
            print(f"\t\t\t {CYAN}{categories[i]}{RESET}")


def print_response(response):
    status = response["Status"]
    msg = response["Message"]
    files = response.get("Files", None)

    if status == "Success":
        status = SUCCESS
    else:
        status = FAIL

    matches = re.findall(regex, msg)
    for match in matches:
        esc_match = re.escape(match)
        msg = re.sub(f"<{esc_match}>", f"{PURPLE}{esc_match}{RESET}", msg)
    msg = msg.replace("\\.", ".")
    msg = msg.replace("\\ ", " ")

    print(f"Status:  {status}")
    print(f"Message: {msg}")
    list_parser(files, FILES)


def upload(campaign, file_path):
    with open(file_path, "rb") as f:
        data = f.read()

    request_json = {
        "command": "upload",
        "campaign": campaign,
        "file_name": file_path.split("/")[-1]
    }

    socket.send_json(request_json, zmq.SNDMORE)
    socket.send(base64.b64encode(data))
    response = socket.recv_json()
    print_response(response)


def download(campaign, file_name):
    request_json = {
        "command": "download",
        "campaign": campaign,
        "file_name": file_name,
    }
    socket.send_json(request_json)

    response = socket.recv_json()
    path = None

    if response.get("Status") == "Success":
        file_data = socket.recv()
        file_data = base64.b64decode(file_data)

        path = os.path.join(BASE_DIR, campaign)
        os.makedirs(path, exist_ok=True)
        path = os.path.join(path, file_name)

        with open(path, "wb") as f:
            f.write(file_data)

    print_response(response)
    if path is not None:
        print(f"\nDownloaded {YELLOW}{path.split('\\')[-1]}{RESET} to {YELLOW}{path}{RESET}")


def list_files(campaign='uploads'):
    request_json = {
        "command": "list",
        "campaign": campaign
    }
    socket.send_json(request_json)

    response_json = socket.recv_json()
    print(campaign)
    if request_json.get("campaign") != f"" or response_json.get(FILES, 0) == 0:
        print_response(response_json)
    else:
        campaigns = response_json.pop("Files")
        list_parser(campaigns, CAMPAIGNS)


if __name__ == "__main__":
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    print(mapping)
    socket.connect(mapping)
    print(f"Connection to {PURPLE}{mapping}{RESET} established.\n")
    os.makedirs(BASE_DIR, exist_ok=True)

    print(f"{YELLOW}{banner.BANNER}{RESET}")
    while True:
        print(f"\n{CYAN}Please select an option from the menu:{RESET}\n"
              f"\t[1]: {PURPLE}Upload a file to the server.{RESET}\n"
              f"\t[2]: {PURPLE}Download a file from the server.{RESET}\n"
              f"\t[3]: {PURPLE}View the contents of a campaign directory.{RESET}\n"
              f"\t[4]: {PURPLE}Exit{RESET}\n")

        option = input(f"Type your selection and press <{GREEN}Enter{RESET}>:{YELLOW}\n=>{RESET} ")

        if option == "1":  # Upload File
            campaign = (input("Enter a campaign name: "))
            upload(campaign, selector())

        elif option == "2":  # Download file
            list_files('')
            campaign_name = input(f"\nPlease type the name of the  campaign directory you "
                                  f"would like to download from and hit {GREEN}Enter{RESET}: \n"
                                  f"If there are no available directories, hit {GREEN}Enter{RESET}, to return to "
                                  f"main menu.\n"
                                  f"{YELLOW}=>{RESET} ")
            if campaign_name != '':
                list_files(campaign_name)
                file_name = input(f"\nPlease type the name of the  file you would like to "
                                  f"download from and hit {GREEN}Enter{RESET}: \n"
                                  f"If you would like to cancel type {GREEN}Enter{RESET}: \n"
                                  f"{YELLOW}=>{RESET} ")
                if file_name != '':
                    download(campaign_name, file_name)

        elif option == "3":  # Get list of assets in campaign directory
            list_files('')
            campaign_name = input(f"\nPlease type the name of the campaign directory you would like to ")
        elif option == "4":
            print(f'\n{YELLOW}=========================================')
            print('[Thank you for using TTRPG Asset Server!]')
            print(f'========================================={RESET}')
            exit(0)
        else:
            print(f"{RED}Error{RESET}: Invalid selection.")

