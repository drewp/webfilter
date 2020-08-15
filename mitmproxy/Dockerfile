FROM mitmproxy/mitmproxy:5.2

WORKDIR /opt
RUN apk add --no-cache tzdata
ENV TZ America/Los_Angeles
ENV LANG en_US.UTF-8

RUN apk add curl py3-pip git iptables strace
RUN pip3 install -U pip

COPY requirements.txt ./
RUN pip3 install --index-url https://projects.bigasterisk.com/ --extra-index-url https://pypi.org/simple -r requirements.txt

#COPY *.py *.html ./

#CMD [ "mitmdump" ]
