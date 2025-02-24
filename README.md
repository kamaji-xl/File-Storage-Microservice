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
> - Instead use `wsl --list --verbose` to get a list of available distros.
> 	- Then run `wsl -d <DistroName>`.Ubuntu-24.04 is reccommended.

### Using Docker

I have included a couple of bash scripts, `build_script.sh` and `stop_and_remove_container.sh`.

To use them first run:

```bash
chmod +x build_script.sh
chmod +x stop_and_remove_container.sh
```

So that they are executable and can then each be ran with `./<FileName>`.

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
>`docker exec -it file_storage_microservice bash` will open a bash shell inside of the container while it's running. Allowing you to use bash commands. This way commands like `ls` can be used to check that files are uploading correctly.

## Using the Server

- Requests are received as `JSON`, and passed to `request_handler(request)` as a dictionary called `request_json`. 
- The handler with then extract `request["command"]` from the request. 
- The server will then call the corresponding function of the command. 
	- `upload(request)`
	- `download(request)`
	- `get_list(request)`

### upload(request)
#### upload(request) - Requesting Data

> [!important]
> - `upload(request)` expects two messages from the socket.
> - The first message should contain the `request_json`.
> - The second should be the file **encoded in base64**.

`request_json` structure for `upload(request)`:

```python
request_json = {  
    "command": "upload",  
    "campaign": campaign_name,  
    "file_name": file_name 
}
```


Example call to `upload(request)`:

```python
socket.send_json(request_json, zmq.SNDMORE)  
socket.send(base64.b64encode(file))
```


#### upload(request) - Receiving Data

`upload(request)` will return one of two messages:

A success message, 

```python
response_json = {  
    "Status": "Success",  
    "Message": f"Downloaded <{file_name}> from <{path}>"  
}
```


or a failure message.

```python
response_json = {  
    "Status": " Failure",  
    "Message": "File not found."
}
```


The message can be received with something like:

```python
response = socket.recv_json()
```

### download(request)

`request_json` structure for `download(request)`:

```python
request_json = {  
    "command": "download",  
    "campaign": campaign_name,  
    "file_name": file_name,  
}
```

### get_list(request)

`request_json` structure for `get_list(request)`:
```python
request_json = {  
    "command": "list",  
    "campaign": campaign_name 
}
```