FROM python:3
ENV PYTHONUNBUFFERED 1

#Directory for saving source code
RUN mkdir /code
WORKDIR /code

#Install all requirements for Django
ADD requirements.txt /code/
RUN pip install -r requirements.txt

#Scripts to ensure connection to Database is established
ADD wait_for_db.sh /code/
ADD db-connect.py /code/
