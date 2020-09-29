import logging
import queue
import threading
import time
import pymysql


class PoolResources(object):

    # max active connections, default -1 which means unlimited
    maxActive = None

    # min idle connections, default 5
    minIdle = None

    # max wait time to get connection source
    maxWait = None

    # save connection instance, use getResource method to get conn instance
    dataSources = None

    # save occupied connections, the connection in this dict means which is current using
    busySources = {}

    def __init__(self, host, port, username, pwd, dbname, maxActive=-1, minIdle=5, maxWait=3):

        self.host = host
        self.port = port
        self.username = username
        self.pwd = pwd
        self.dbname = dbname

        if isinstance(maxActive, int):
            self.maxActive = maxActive
        else:
            raise Exception("maxActive value error, must be int")

        if isinstance(minIdle, int):
            self.minIdle = minIdle
        else:
            raise Exception("minIdle value error, must be int")

        if isinstance(maxWait, int):
            self.maxWait = maxWait
        else:
            raise Exception("maxWait value error, must be int")

        self.dataSources = queue.Queue(maxsize=self.maxActive)
        self.initPool()

    def connectionInstance(self):
        """
        create database connection instance
        :return: A Connection Object
        """
        try:
            conn = pymysql.connect(self.host, self.username, self.pwd, self.dbname)
        except pymysql.DatabaseError as error:
            raise error
        else:
            return conn

    def initPool(self):
        """
        init connection pool, set the minIdle connection instances in dataSources
        :return:
        """
        if self.dataSources.qsize() == 0:
            for _ in range(0, self.minIdle):
                self.dataSources.put_nowait(self.connectionInstance())
            logging.info("init pool successfully, current size: {}".format(self.currentSize))

    @property
    def currentSize(self):
        """
        :return: the number of idle connections
        """
        return self.dataSources.qsize()

    @property
    def busySize(self):
        """
        :return: the number of occupied connections
        """
        return len(self.busySources)

    def addInstance(self):
        """
        add connection instances when there are no idle connection instances
        :return:
        """
        if self.maxActive > 0 and self.currentSize + len(self.busySources) <= self.maxActive:
            return self.connectionInstance()
        else:
            raise Exception("no available resources, pool is full")

    def getResource(self):
        """
        get connection instance from pool
        :return: A Connection Object
        """
        currentThread = threading.current_thread().getName()
        try:
            instance = self.dataSources.get(timeout=self.maxWait)
        except queue.Empty:
            instance = self.addInstance()
            self.busySources[currentThread] = instance
            return self.busySources[currentThread]
        else:
            self.busySources[currentThread] = instance
            return self.busySources[currentThread]

    def release(self):
        """
        return the connection into the pool
        :return:
        """
        currentThread = threading.current_thread().getName()
        try:
            self.dataSources.put_nowait(self.busySources.pop(currentThread))
        except Exception as error:
            raise error

    def close(self):
        """
        close all the connections in pool and busySources
        :return:
        """
        if self.busySources.__sizeof__() > 0:
            for conn in self.busySources:
                try:
                    self.busySources.pop(conn).close()
                except pymysql.DatabaseError as close_e:
                    raise close_e

        while True:
            try:
                conn2 = self.dataSources.get()
            except queue.Empty:
                self.dataSources = None
                break
            else:
                try:
                    conn2.close()
                except pymysql.DatabaseError as close_e:
                    raise close_e


if __name__ == '__main__':
    ip = '10.13.4.16'
    username = 'test_account'
    pwd = 'YS5boBtGfkVpO3pb'
    dbname = 'woody_test_db'
    pool = PoolResources(ip, 3306, username, pwd, dbname, maxActive=20, minIdle=5, maxWait=1)
    time.sleep(5)
