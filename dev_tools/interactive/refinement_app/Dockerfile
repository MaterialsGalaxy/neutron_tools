FROM rocker/shiny

# Add user an change working directory and user

RUN sudo apt-get update && apt-get install -y python3-pip net-tools w3m
WORKDIR /srv/shiny-server
# Install requirements
COPY requirements.txt .
RUN pip install --upgrade -r requirements.txt

# Copy the app
# COPY . .

ARG PORT=8765
ARG LOG_PATH=/tmp/gxit.log

ENV LOG_PATH=$LOG_PATH
ENV PORT=$PORT

# Edit shiny-server config
RUN cat /etc/shiny-server/shiny-server.conf \
    | sed "s/3838/${PORT}/" > /etc/shiny-server/shiny-server.conf.1
RUN mv /etc/shiny-server/shiny-server.conf.1 /etc/shiny-server/shiny-server.conf

RUN sed -i -e '1ipython /usr/bin/python3;\' /etc/shiny-server/shiny-server.conf

RUN mkdir -p $(dirname "${LOG_PATH}")
EXPOSE $PORT

# copy the app source and GSASII
COPY src/ ./
COPY GSASII /srv/shiny-server/GSASII
ENV PATH="$PATH:/srv/shiny-server/GSASII/"

COPY src/shiny-server.sh /usr/bin/shiny-server.sh
RUN chmod 777 /usr/bin/shiny-server.sh

RUN sudo mkdir -p /var/shiny-server/shiny_test/work && \
    sudo chown shiny:shiny /var/shiny-server/shiny_test/work &&\
    sudo chown shiny:shiny /srv/shiny-server

CMD ["/bin/sh", "-c", "shiny-server > ${LOG_PATH} 2>&1"]
