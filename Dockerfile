FROM bang6:5000/base_x86

WORKDIR /opt

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata

#RUN wget https://snapshots.mitmproxy.org/5.0.1/mitmproxy-5.0.1-linux.tar.gz
#RUN aunpack mitmproxy-5.0.1-linux.tar.gz

COPY requirements.txt ./
RUN pip3 install --index-url https://projects.bigasterisk.com/ --extra-index-url https://pypi.org/simple -r requirements.txt
RUN pip3 install -U 'https://github.com/drewp/cyclone/archive/python3.zip?v3'

#COPY *.py *.html *.css *.js *.n3 ./

CMD [ "mitmdump" ]
