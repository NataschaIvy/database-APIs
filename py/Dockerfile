FROM tiangolo/uwsgi-nginx-flask:python3.8

#install system packages
RUN apt-get update && apt-get install -y \
    libpq-dev \
    python-dev \
    && rm -rf /var/lib/apt/lists/*

#install python packages
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt