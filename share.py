import os
import argparse
import logging
import random
import string
import sys
import socket
from urllib.parse import quote, unquote

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
import uvicorn

app = FastAPI()
shared_roots = []
unique_url = ""


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def generate_short_url(length=6):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't have to be reachable
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def add_shared_paths(paths):
    shared_paths = []
    for path in paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            shared_paths.append(abs_path)
            logging.info(f"Added to shared paths: {abs_path}")
        else:
            logging.warning(f"Path does not exist and will be skipped: {path}")
    return shared_paths


def is_subpath(path, directory):
    # Ensure that the path is within the directory to prevent directory traversal
    path = os.path.abspath(path)
    directory = os.path.abspath(directory)
    return os.path.commonpath([path, directory]) == directory


@app.get("/", response_class=HTMLResponse)
async def read_root():
    return (
        "<html><body><h2>Welcome to the P2P File Sharing Tool</h2>"
        "<p>Please use the provided link to access the shared files:</p>"
        f"<p><a href='/{unique_url}/'>Go to Shared Files</a></p>"
        "</body></html>"
    )


@app.get("/favicon.ico")
async def favicon():
    return HTMLResponse(status_code=204)


@app.get("/{unique_url}/", response_class=HTMLResponse)
async def list_root():
    content = "<html><body><h2>Shared Directories:</h2><ul>"
    for root in shared_roots:
        root_relative = os.path.basename(root.rstrip("/"))
        root_quoted = quote(root_relative)
        content += f'<li><a href="/{unique_url}/{root_quoted}/">{root_relative}/</a></li>'
    content += "</ul></body></html>"
    return content


@app.get("/{unique_url}/{path:path}")
async def serve_path(path: str):
    path = unquote(path)
    for root in shared_roots:
        root_relative = os.path.basename(root.rstrip("/"))
        if path == root_relative or path.startswith(root_relative + '/'):
            # Construct the relative path within the root
            relative_path = path[len(root_relative):].lstrip('/')
            abs_path = os.path.join(root, relative_path)
            abs_path = os.path.abspath(abs_path)
            if is_subpath(abs_path, root) and os.path.exists(abs_path):
                if os.path.isdir(abs_path):
                    # List directory contents
                    content = f"<html><body><h2>Index of /{unique_url}/{path}/</h2><ul>"
                    # Add parent directory link if not at root
                    parent_path = '/'.join(path.strip('/').split('/')[:-1])
                    if parent_path:
                        parent_quoted = quote(parent_path)
                        content += f'<li><a href="/{unique_url}/{parent_quoted}/">.. (parent directory)</a></li>'
                    else:
                        content += f'<li><a href="/{unique_url}/">.. (parent directory)</a></li>'
                    entries = os.listdir(abs_path)
                    for entry in sorted(entries):
                        entry_full_path = os.path.join(abs_path, entry)
                        entry_path = os.path.join(path, entry)
                        entry_quoted = quote(entry_path)
                        if os.path.isdir(entry_full_path):
                            content += f'<li><a href="/{unique_url}/{entry_quoted}/">{entry}/</a></li>'
                        else:
                            content += f'<li><a href="/{unique_url}/{entry_quoted}">{entry}</a></li>'
                    content += "</ul></body></html>"
                    return HTMLResponse(content=content)
                elif os.path.isfile(abs_path):
                    logging.info(f"Serving file: {abs_path}")
                    return FileResponse(
                        path=abs_path,
                        filename=os.path.basename(abs_path),
                        media_type="application/octet-stream",
                    )
            else:
                logging.warning(f"Access denied or path not found: {abs_path}")
                raise HTTPException(status_code=404, detail="File or directory not found")
    logging.warning(f"Path not found in shared roots: {path}")
    raise HTTPException(status_code=404, detail="File or directory not found")


def share_files_http(paths, port=6688, custom_url=None):
    global unique_url, shared_roots
    unique_url = custom_url if custom_url else generate_short_url()
    shared_roots = add_shared_paths(paths)

    if not shared_roots:
        logging.error("No valid files or directories to share.")
        sys.exit(1)

    access_url = f"http://{get_local_ip()}:{port}/{unique_url}/"
    logging.info(f"Files available at: {access_url}")

    try:
        uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
    except KeyboardInterrupt:
        logging.info("Shutting down the server...")


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="P2P file sharing tool with web support")
    parser.add_argument("paths", nargs="+", help="Files or directories to share")
    parser.add_argument("--port", type=int, default=6688, help="Port to serve on")
    parser.add_argument("--url", type=str, help="Custom URL path segment")
    args = parser.parse_args()

    share_files_http(args.paths, args.port, args.url)


if __name__ == "__main__":
    main()

