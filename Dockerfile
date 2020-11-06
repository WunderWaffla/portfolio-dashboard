FROM python:3-slim-buster
WORKDIR /src
COPY requirements.txt /opt/backup/requirements.txt
COPY requirements.txt /src/
RUN pip install -r requirements.txt
COPY main.py config.yml google-app-config.json /src/
ENTRYPOINT ["python", "-u", "/src/main.py"]
