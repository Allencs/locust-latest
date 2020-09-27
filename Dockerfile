FROM locust:1.2.3

RUN pip install pymysql

ENTRYPOINT ["locust"]

# turn off python output buffering
ENV PYTHONUNBUFFERED=1