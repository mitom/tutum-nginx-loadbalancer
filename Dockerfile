 FROM nginx:1.9.9

RUN echo "daemon off;" >> /etc/nginx/nginx.conf

RUN apt-get update
RUN apt-get install -y python

ADD https://bootstrap.pypa.io/get-pip.py /tmp/get-pip.py
RUN python /tmp/get-pip.py
RUN rm -f /tmp/get-pip.py
RUN pip install python-tutum mako

ADD https://github.com/chrismytton/shoreman/raw/master/shoreman.sh /bin/shoreman
RUN chmod 0755 /bin/shoreman


COPY conf /opt/
COPY Procfile /opt/
Copy nginx_reload.py /opt/

WORKDIR /opt/

CMD ["shoreman"]