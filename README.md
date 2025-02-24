# Getting Started
## Dependencies

The File-Storage-Microservice consists of two main files. `server.py` and `client.py`. Before, you run anything first make sure you have the necessary packages installed. I believe everything that isn't already "builtin" to python can be found in the `requirements.txt` file. 

If you will be using a virtual environment:

```powershell
python -m venv venv

source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate  # On Windows

pip install -r requirements.txt

```

Run the command below to install the packages globally.

```powershell
pip install -r requirements.txt
```

## client.py

- To run `client.py` simply run it like you would any other python program. 

## server.py

You have a couple of options for running `server.py`.

- The first is to run normally. 
- The second is to use the included `Dockerfile`.

I recommend using the `Dockerfile`. It comes with the advantage that the storage is ephemeral unless you attach a volume for permanence. Meaning that every time you stop the container whatever files have been uploaded will be erased, and it's really convenient not having to constantly clear out all your test files. The code is preconfigured for docker, however you can easily ignore it by setting `CONTAINERIZED=FALSE` in the `.env` file. 

>[!important] 
> - `CONTAINERIZED=True` isn't an actual boolean variable.
> - I have explained further in the `.env` comments. 

### [I don't want to use docker, show me how the API works](#Using-the-Server)

##  Docker

### Installation

- Docker can be installed by navigating to [the docker website](https://www.docker.com/products/docker-desktop/), and installing  docker desktop. 
- If you don't have WSL installed, **install it first**, to save the headache of some trouble shooting later.
	- If you are on mac or Linux then you can ignore this.  


> [!note] 
> If you have already installed docker desktop before WSL. 
> - **DO NOT INSTALL WSL WITH** `wsl --install` 
> - Instead, use `wsl --list --verbose` to get a list of available distros.
> 	- Then run `wsl -d <DistroName>`.
> 	- Ubuntu-24.04 is recommended.


### Using Docker

- First ensure that docker desktop is running.
- I have included a couple of bash scripts:
	- `build_script.sh` 
	- `stop_and_remove_container.sh`

To use them first run:

```bash
chmod +x build_script.sh
chmod +x stop_and_remove_container.sh
```
<br>
So that they are executable and can then each be ran with `./<FileName`.

> [!note]
> If you are using WSL and are getting `-bash: ./<ScriptName>.sh: cannot execute: required file not found`. 
> - Try installing `dos2unix` with `sudo apt install dos2unix` (on Ubuntu).
> - Then run `dos2unix <ScriptName>.sh` and try running the script again.

<br>

#### build_script.sh

- This will first stop and remove any active containers with `$CONTAINER_NAME`. 
- It will then build and run the container from the `Dockerfile`.
- Afterwards it will run `docker logs -f $CONTAINER_NAME`.
	- This makes it so that the server output is displayed in the terminal. 
	- You can exit the logging with `CNTRL+C`, this will just stop the logging and kick you back to your `pwd`. The container will still be running in the background. 
- At this point the server will be listening on `tcp//:0.0.0.0:5555`.
	- Requests made by the client on `tcp//:localhost:6000`, will be received by the container and responses will be sent to the client.

#### stop_and_remove_container.sh

- Basically, this is just the first portion of `build_scripts.sh`. 
- Any container with the matching `$CONTAINER_NAME` will be stopped and removed. 

>[!tip] 
>`docker exec -it file_storage_microservice bash` will open a bash shell inside of the container while it's running. 
>- Allowing you to use bash commands. 
>- This way commands like `ls` can be used to check that files are uploading correctly.
>- Logs can also be viewed in docker desktop.

<br>

## Using the Server

- Requests are received as `JSON`, and passed to `request_handler(request)` as a dictionary called `request_json`. 
- The handler with then extract `request["command"]` from the request. 
- The server will then call the corresponding function of the command. 
	- `upload(request)`
	- `download(request)`
	- `get_list(request)`

### upload(request)

When called will upload a single file to the server, and send a response in `JSON` format.

#### upload(request) - Requesting Data


> [!important]
> - `upload(request)` expects two messages from the socket.
> - The first message should contain the `request_json`.
> - The second should be the file **encoded in base64**.

<br>

`request_json` structure for `upload(request)`:

```python
request_json = {  
    "command": "upload",  
    "campaign": campaign_name,  
    "file_name": file_name 
}
```

<br>

Example call to `upload(request)`:

```python
socket.send_json(request_json, zmq.SNDMORE)  
socket.send(base64.b64encode(file))
```

<br>

#### upload(request) - Receiving Data

`upload(request)` will return one of two messages:

**Success Message**:

```python
response_json = {  
    "Status": "Success",  
    "Message": f"Downloaded <{file_name}> from <{path}>"  
}
```

<br>

**Failure Message**:

```python
response_json = {  
    "Status": " Failure",  
    "Message": "File not found."
}
```


The message can be received by assigning a variable to `socket.recv_json()`.

<br>

**Example**:

```python
response = socket.recv_json()
```

<br>

### download(request)

When called check to see if the requested file exists. If the file exists it will then send a message in `JSON` format followed by a second message containing the requested file encoded in base64. Otherwise, only one message stating the failure of the operation will be sent.

#### download(request) - Requesting Data

`request_json` structure for `download(request)`:

```python
request_json = {  
    "command": "download",  
    "campaign": campaign_name,  
    "file_name": file_name,  
}
```

##### An example request:

```python
socket.send_json(request_json)
```

#### download(request) - Receiving Data

>[!important]
> `download(request)` sends two messages if the requested file exists.
> - The first message is the response in `JSON` format.
> 	- If the file doesn't exist this will be the only message sent.
> - The second message is the file data **encoded in base64**.

#### If the file exists:

##### First Message:

```python
response_json = {  
    "Status": "Success",  
    "Message": f"Downloading <{file_name}> from <{path}>",  
}

# response_json is sent with zmq.SNDMORE 
socket.send_json(response_json, zmq.SNDMORE)
```


##### Second Message:

```python
# File data is encoded in base64
encoded_data = base64.b64encode(file_content)

# Then sent
socket.send(encoded_data)
```

#### If the file doesn't exist:

```python
response_json = {
    "Status": " Failure",  
    "Message": "File not found."
}

# response_json is sent
socket.send_json(response)
```

#### Receiving data example:

```python
# Receive first message
response = socket.recv_json()

# If the status is "Success" receive the data
file_data = socket.recv()

# Then decode the data using base64.b64decode()
file_data = base64.b64decode(file_data)
```

### get_list(request)

`request_json` structure for `get_list(request)`:

```python
request_json = {  
    "command": "list",  
    "campaign": campaign_name 
}
```



