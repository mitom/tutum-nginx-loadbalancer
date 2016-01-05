# tutum-nginx-loadbalancer

The purpose of this image is to dynamically add/remove containers to/from nginx as they become available in tutum.
It provides **NO** default configuration for nginx, but gives you the ability to write your own using simple templating.

For this to have any meaning you must handle redeploying your containers in a way that they are never all down at the same time.
Check out my [script](https://github.com/mitom/tutum-rolling-redeploy) for this issue.

## Usage

First of, create the service you will want to load balance in tutum. No need to start it, just make sure it exists.

Then create your load balancer from this image, either give it full access, or set `TUTUM_USER` and `TUTUM_APIKEY` to your username and apikey.
Set `LB_SERVICE` to the *uuid* of the service you want to loadbalance.
You can find this if you navigate to your service in the tutum web interface and look at the url. It will be something like
`https://dashboard.tutum.co/container/service/show/<this is the uuid you are looking for>/`

It is not required to link the containers.

You will have to provide your own configuration for nginx and mount these on `/opt/conf/` in the load balancer.

**But** I would recommend to create your own image based on this one, where you ship the configs with it.

The files are interpretted as [mako](http://www.makotemplates.org/) templates, with the only variable being `containers`, a list of the *running* containers in the service you specified.
The whole container object is accessible, as described in the [tutum api docs](https://docs.tutum.co/v2/api/#container).
Every `.conf` file in `/opt/conf/` will be used.

This is a simple example on how to create an upstream from your containers:

````
upstream backend {
% for container in containers:
    server ${container.private_ip}:8080;
% endfor
}
````

Optionally, you may set `GRACE_PERIOD` to a number (of seconds) to wait before reloading nginx, to give your service some time to start.