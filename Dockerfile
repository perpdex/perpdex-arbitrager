FROM python:3.8.12

RUN \
  curl -o /usr/bin/wait-for-it.sh https://raw.githubusercontent.com/vishnubob/wait-for-it/81b1373f17855a4dc21156cfe1694c31d7d1792e/wait-for-it.sh \
  && chmod +x /usr/bin/wait-for-it.sh

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r /tmp/requirements.txt
