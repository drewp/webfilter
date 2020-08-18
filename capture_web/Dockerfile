FROM ubuntu:eoan-20200608

WORKDIR /opt

ENV TZ=America/Los_Angeles
ENV LANG=en_US.UTF-8

RUN apt update

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata

RUN apt-get install -y python3-nftables strace wget curl vim-tiny python3-pip
RUN pip3 install -U pip
RUN apt-get install -y git

COPY requirements.txt ./
RUN pip3 install --index-url https://projects.bigasterisk.com/ --extra-index-url https://pypi.org/simple -r requirements.txt
RUN pip3 install -U 'https://github.com/drewp/cyclone/archive/python3.zip?v3'

RUN apt-get install -y iptables

COPY *.py *.sh ./
COPY frontend/build build/
COPY frontend/index.html index.html

CMD [ "/bin/sh", "entrypoint.sh" ]
