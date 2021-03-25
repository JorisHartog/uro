FROM python:3.9

COPY . /usr/src/app
WORKDIR /usr/src/app

RUN apt update
RUN apt install -y gdb nasm vim

CMD [ "/bin/bash" ]
