import tutum
import websocket
import base64
import os
import json
import re
import sys
import time
from mako.template import Template
from subprocess import call


service_uuid = os.environ.get('LB_SERVICE')
username = os.environ.get('TUTUM_USER')
apikey = os.environ.get('TUTUM_APIKEY')
tutum_auth = os.environ.get('TUTUM_AUTH')
grace_period = float(os.environ.get('GRACE_PERIOD') or 0)

if (not (username and apikey) and not tutum_auth):
    raise EnvironmentError('You should either give full access to this service, or provide TUTUM_USER and TUTUM_APIKEY as env variables')
if (not service_uuid):
    raise EnvironmentError('You must set the LB_SERVICE env var.')

service_full = '/api/v1/service/'+service_uuid+'/'
container_uuid_re = re.compile(r"\/api\/v1\/container\/(.+)\/")
nginx_config_dir = '/etc/nginx/conf.d/'
containers = {}

def rewrite_config():
    base_dir = '/opt/conf'
    for i in os.listdir(base_dir):
        if i.endswith(".conf"):
            template = Template(filename=base_dir + '/' + i)
            rendered = template.render(containers=containers.values())
            with open(nginx_config_dir + i, 'w') as f:
                f.write(rendered)
    sys.stdout.write("Rewrote configs, reloading nginx\n")
    call(["nginx", "-s", "reload"])

def get_container(uuid):
    return tutum.Container.fetch(uuid)


def get_container_uuid(uri):
    match = container_uuid_re.match(uri)
    if (not match):
        raise ValueError("Invalid uri, couldn't find uuid")

    return match.group(1)

def add_container(uri):
    if uri in containers:
        return

    container = get_container(get_container_uuid(uri))
    containers[uri] = container
    if (grace_period):
        print "Waiting " + str(grace_period) + " seconds (grace period)"
        time.sleep(grace_period)
    sys.stdout.write("Adding " + container.name + "\n")
    rewrite_config()

def remove_container(uri):
    if uri not in containers:
        return


    container = containers[uri]
    del containers[uri]
    sys.stdout.write("Removing " + container.name + "\n")

    rewrite_config()

def on_message(ws, message):
    message = json.loads(message)
    if message['type'] == 'container' and service_full in message['parents']:
        if message['state'] == 'Running':
            add_container(message['resource_uri'])
        if message['state'] in ['Stopping', 'Stopped', 'Terminating']:
            remove_container(message['resource_uri'])

def on_error(ws, error):
    sys.stderr.write(error)

def on_close(ws):
    sys.stdout.write("### stream closed ###\n")

def on_open(ws):
    sys.stdout.write("### stream opened ###\n")


if (tutum_auth):
    header = "Authorization: " + tutum_auth
else:
    header = "Authorization: Basic %s" % base64.b64encode("%s:%s" % (username, apikey))


ws = websocket.WebSocketApp('wss://stream.tutum.co/v1/events',
                            header=[header],
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close,
                            on_open=on_open
)

existing_containers = tutum.Container.list(service=service_full)
for container in existing_containers:
    if container.state in ['Running', 'Starting', 'Creating']:
        containers[container.resource_uri] = container

sys.stdout.write("Found " + str(len(containers)) + " containers\n")
rewrite_config()


ws.run_forever()