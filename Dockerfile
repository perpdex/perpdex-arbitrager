FROM python:3.8.12

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r /tmp/requirements.txt
