FROM bang5:5000/base_basic

WORKDIR /opt

RUN apt-get install -y strace wget git

COPY requirements.txt ./
RUN pip3 install --index-url https://projects.bigasterisk.com/ --extra-index-url https://pypi.org/simple -r requirements.txt
RUN pip3 install -U 'https://github.com/drewp/cyclone/archive/python3.zip?v3'

COPY package.json ./
RUN pnpm install

COPY rollup.config.js ./
COPY src/ ./src
RUN pnpm run build

COPY *.py *.json ./

CMD [ "/usr/bin/python3", "net_route_input.py", "-v" ]
