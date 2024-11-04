# 
## Overview
This tool is a file sharing application built using FastAPI and Uvicorn. It allows you to quickly share files and directories over a local network. By running a simple Python script, you can serve files and directories, enabling others to access and download them through a web browser.

### Wanring: Its primirily built for small/internal/home setup. (Once you share anything, its available over the network). Not recommanded for use over internet. 

### Installation Requirements

```
pip install fastapi uvicorn
```

## Usage
```
python3 share.py /path/to/directory_or_file1
```

## Example:
```
python3 share.py /home/foobar/photos/
```

## Optional Flags:

### url:
```
--url: This to pre-define the download URL, if not used a random URL will be provided.
```

### port:
```
--port:  To specify a custom port number (default is 6688), use the --port flag.
```

## Example Complete Usage:

```
python3 share.py /home/foobar/photos/ --port 8080  --url family-photos
```


### Example Output on Terminal: 

In the following example, Anyone in the LAN can download the files via ``` http://192.168.1.174:8080/family-photos/``` URL.
```
python3 share.py /home/foobar/photos/ --port 8080  --url family-photos
2024-11-04 12:58:53,647 - INFO - Added to shared paths: /home/foobar/photos/
2024-11-04 12:58:53,647 - INFO - Files available at: http://192.168.1.174:8080/family-photos/
INFO:     Started server process [16912]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

