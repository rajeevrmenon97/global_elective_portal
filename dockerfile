from ubuntu

#Install python3
RUN apt-get update -y \
    && apt-get install software-properties-common -y \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update -y\
    && apt-get install python3.6

#Install pip
RUN apt-get update -y \
    && apt-get install python-pip python-dev build-essential -y 

#Install django
RUN pip install Django

#Install vim
RUN apt-get install vim -y

#Install mysql client
RUN apt-get install python-setuptools -y
RUN apt-get install libmysqlclient-dev -y
RUN pip install mysqlclient
RUN pip install PyMySQL

#Install mysql server
RUN apt-get install mysql-server -y \
    && mysql_secure_installation

#Install postgres client
RUN pip install psycopg2

#Install postgres server
RUN apt-get install postgresql postgresql-contrib \
    && update-rc.d postgresql enable \
    && service postgresql start \
    && postgres psql -c "CREATE USER devika WITH PASSWORD 'devika123' CREATEDB" \
    && postgres psql -c "CREATE DATABASE global_elective_portal"

#Copy project
WORKDIR /home/root
RUN mkdir gep
WORKDIR ./gep
COPY $PWD/gep_project ./gep_project

CMD "python ./gep_project/manage.py runserver 127.0.0.1:8000"
