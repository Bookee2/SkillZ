"""Run a Capra Unreal Python file through the editor's local remote execution port.

The script is first copied into the Unreal project's Saved directory so macOS
does not prompt the editor for access to the Desktop checkout.
"""
import json
import os
import shutil
import socket
import sys
import time
from pathlib import Path

PROJECT_ROOT=Path(os.environ.get('UNREAL_PROJECT_ROOT','/Users/kb/Documents/Unreal Projects/Capra_intro')).resolve()
PROJECT_SAVED=PROJECT_ROOT/'Saved/CapraStudy'
PROJECT_NAME=os.environ.get('UNREAL_PROJECT_NAME',PROJECT_ROOT.name)
REMOTE_GROUP,REMOTE_PORT=os.environ.get('UNREAL_REMOTE_GROUP','239.0.0.1:6766').split(':')
REMOTE_PORT=int(REMOTE_PORT)
COMMAND_PORT=int(os.environ.get('UNREAL_COMMAND_PORT','6776'))
ENGINE_PY=Path('/Volumes/KB SS/Unreal Engine/UE_5.8/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python')
sys.path.insert(0,str(ENGINE_PY))
import remote_execution

def local_socket(self):
    sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEPORT,1)
    sock.bind(('',REMOTE_PORT))
    sock.setsockopt(socket.IPPROTO_IP,socket.IP_MULTICAST_LOOP,1)
    sock.setsockopt(socket.IPPROTO_IP,socket.IP_MULTICAST_TTL,0)
    sock.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,
        socket.inet_aton(REMOTE_GROUP)+socket.inet_aton('127.0.0.1'))
    sock.settimeout(.1)
    self._broadcast_socket=sock

def local_send(self,message):
    self._broadcast_socket.sendto(message.to_json_bytes(),('127.0.0.1',REMOTE_PORT))

remote_execution._RemoteExecutionBroadcastConnection._init_broadcast_socket=local_socket
remote_execution._RemoteExecutionBroadcastConnection._broadcast_message=local_send

source=Path(sys.argv[1]).resolve()
assert source.is_file(),source
PROJECT_SAVED.mkdir(parents=True,exist_ok=True)
destination=PROJECT_SAVED/source.name
if source != destination:shutil.copy2(source,destination)
config=remote_execution.RemoteExecutionConfig()
config.multicast_group_endpoint=(REMOTE_GROUP,REMOTE_PORT)
config.command_endpoint=('127.0.0.1',COMMAND_PORT)
client=remote_execution.RemoteExecution(config)
client.start()
try:
    for _ in range(40):
        nodes=[n for n in client.remote_nodes if n.get('project_name')==PROJECT_NAME and Path(n.get('project_root','')).resolve()==PROJECT_ROOT]
        if nodes:break
        time.sleep(.25)
    if not nodes:raise RuntimeError(f'{PROJECT_NAME} editor not discovered at {PROJECT_ROOT}')
    client.open_command_connection(nodes[0]['node_id'])
    result=client.run_command(str(destination),exec_mode=remote_execution.MODE_EXEC_FILE,raise_on_failure=True)
    print(json.dumps(result))
finally:
    client.stop()
