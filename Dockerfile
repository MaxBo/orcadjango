FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.2
RUN apt-get -y update \
    && apt-get install -y ca-certificates curl gnupg apt-utils software-properties-common

RUN add-apt-repository ppa:deadsnakes/ppa

RUN mkdir -p /etc/apt/keyrings
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg
RUN echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list

RUN curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
RUN echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" | tee /etc/apt/sources.list.d/pgdg.list

RUN apt -y update \
    && apt -y upgrade \
    && apt -y install git wget zip \
    && apt -y install nodejs yarn \
    && apt -y install python3.10 \
    && apt -y install python3-pip python3-pyproj python3-venv \
    && apt -y install libpq-dev libkml-dev \
    && apt -y install binutils libproj-dev libgeos-dev \
    && apt -y install libsqlite3-mod-spatialite libsqlite3-dev \
    && apt -y install osmium-tool \
    && apt -y install default-jre \
    && apt -y install xxd \
    && apt -y install postgresql-client

RUN wget -O /tmp/osmosis.tar https://github.com/openstreetmap/osmosis/releases/download/0.49.2/osmosis-0.49.2.tar \
    && tar xvf /tmp/osmosis.tar -C /opt \
    && rm /tmp/osmosis.tar \
    && mv /opt/osmosis-0.49.2 /opt/osmosis \
    && chmod a+x /opt/osmosis/bin/osmosis

RUN git clone https://github.com/MaxBo/orcadjango.git /orcadjango
RUN git clone -b feature/function_descriptions https://github.com/MaxBo/miraculix-orca.git /tools

RUN npm i npm@latest -g
RUN npm i -g @angular/cli@15

# bundle the frontend scripts
WORKDIR /orcadjango/web-frontend
RUN npm install
RUN ng build --stats-json --build-optimizer
RUN rm -r node_modules
RUN rm -r /usr/lib/node_modules/@angular/cli/node_modules/tmp/

WORKDIR /orcadjango
RUN python3 -m venv /opt/.venv \
    && . /opt/.venv/bin/activate \
    && python -m pip install gdal==3.8 \
    && python -m pip install -r requirements.txt \
    && python -m pip install -r /tools/extractiontools/requirements.txt


#RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt

#RUN mkdir -p /datentool/public/media
# django demands a secret key (not set in settings due to security reasons)
#ENV SECRET_KEY=1234
#RUN python manage.py collectstatic
# unset the key
ENV SECRET_KEY=""