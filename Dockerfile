FROM python:3.6

ENV TZ Asia/Shanghai

RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install nodejs -y

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
ADD requirements.txt /usr/src/app

RUN pip install --upgrade pip && pip install -r requirements.txt

ADD ./telescope /usr/src/app

EXPOSE 35556

ENTRYPOINT ["bash", "/usr/src/app/start.sh"]
