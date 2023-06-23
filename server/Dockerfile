FROM python:3.11

COPY server.py /code/

WORKDIR /code

RUN pip install flask

ENTRYPOINT [ "python" ]

CMD [ "klaatu_server.py" ]