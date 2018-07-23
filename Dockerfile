FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
RUN apt-get update -y \ 
    && apt-get install net-tools -y
ADD wait_for_db.sh /code/
ADD db-connect.py /code/
