import logging
import queue
import threading
import time

import pymysql


class PoolResources(object):

    # 最大活动连接数
    maxActive = None

    # 最小空闲连接数
    minIdle = None

    # 最大等待时间
    maxWait = None

    dataSources = None

    busySources = {}

    def __init__(self, host, port, username, pwd, dbname, maxActive=None, minIdle=None, maxWait=None):

        self.host = host
        self.port = port
        self.username = username
        self.pwd = pwd
        self.dbname = dbname

        if maxActive is not None:
            try:
                float(maxActive)
                self.maxActive = maxActive
            except ValueError as max_active_e:
                raise Exception("{}, maxActive value error, should be int".format(max_active_e))
        else:
            self.maxActive = -1

        if minIdle is not None:
            try:
                float(minIdle)
                self.minIdle = minIdle
            except ValueError as min_idle_e:
                raise Exception("{}, minIdle value error, should be int".format(min_idle_e))
        else:
            self.minIdle = 5

        if maxWait is not None:
            try:
                float(maxWait)
                self.maxWait = maxWait
            except ValueError as max_wait_e:
                raise Exception("{}, maxWait value error, should be int".format(max_wait_e))
        else:
            self.maxWait = 1

        self.dataSources = queue.Queue(maxsize=self.maxActive)
        self.initPool()

    def connectionInstance(self):
        try:
            conn = pymysql.connect(self.host, self.username, self.pwd, self.dbname)
        except pymysql.DatabaseError as error:
            raise error
        else:
            return conn

    def initPool(self):
        if self.dataSources.qsize() == 0:
            for _ in range(0, self.minIdle):
                self.dataSources.put_nowait(self.connectionInstance())
            logging.info("init pool successfully, current size: {}".format(self.currentSize))

    @property
    def currentSize(self):
        return self.dataSources.qsize()

    @property
    def busySize(self):
        return len(self.busySources)

    def addInstance(self):
        if self.maxActive > 0 and self.currentSize + len(self.busySources) <= self.maxActive:
            return self.connectionInstance()
        else:
            raise Exception("no available resources, pool is full")

    def getResource(self):
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
        currentThread = threading.current_thread().getName()
        try:
            self.dataSources.put_nowait(self.busySources.pop(currentThread))
        except Exception as error:
            raise error

    def close(self):
        print("xiaohui")
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
    ip = '192.168.3.20'
    username = 'root'
    pwd = '123456'
    pool = PoolResources(ip, 3306, username, pwd, "allen_mix", maxActive=20, minIdle=5, maxWait=1)
    time.sleep(5)
















