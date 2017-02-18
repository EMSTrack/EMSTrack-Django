FROM python:3.4
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN apt-get update
RUN apt-get install -y gdal-bin python-gdal python3-gdal
RUN apt-get install -y libgdal-dev
RUN pip3 install -r requirements.txt
ADD . /code/
RUN apt-get install -y binutils libproj-dev gdal-bin

