FROM python:3.13

WORKDIR /app

COPY . /app

ENTRYPOINT [ "python", "main.py" ]