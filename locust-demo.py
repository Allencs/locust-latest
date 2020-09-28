import datetime
import logging
import os
import threading
import time
import traceback
from pypool import PoolResources
import pymysql
from locust import task, TaskSet, User, events, between


@events.user_error.add_listener
def user_error(user_instance, exception, tb):
    print("%r, %s, %s" % (user_instance, exception, "".join(traceback.format_tb(tb))))


@events.spawning_complete.add_listener
def spawning_complete(user_count):
    print("HaHa, Locust have generate %d users" % user_count)


@events.test_stop.add_listener
def on_test_stop(**kwargs):
    # pool.close()
    print("A new test is ending")


class MyClient(object):

    _locust_environment = None

    def __init__(self):
        self.collection = {}

    def setCollection(self, value):
        name = threading.current_thread().getName()
        self.collection[name] = value
        return self.collection[name]

    def showTime(self):
        start_time = time.time()
        try:
            # strTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            strTime = datetime.datetime.now()
            self.setCollection(strTime)
        except Exception as error:
            total_time = int((time.time() - start_time) * 1000)
            self._locust_environment.events.request_failure.fire(request_type="PrivateProtocol",
                                                                 name='showTime',
                                                                 response_time=total_time,
                                                                 exception=error,
                                                                 response_length=0)
            raise error
        else:
            total_time = int((time.time() - start_time) * 1000)
            self._locust_environment.events.request_success.fire(request_type="PrivateProtocol",
                                                                 name='showTime',
                                                                 response_time=total_time,
                                                                 response_length=0)

        logging.info("set time --> {}".format(strTime))


ip = '192.168.3.20'
username = 'root'
pwd = '123456'

pool = PoolResources(ip, 3306, username, pwd, "allen_mix", maxActive=20, minIdle=5, maxWait=1)


class MySqlClient(object):
    _locust_environment = None

    # ip = '192.168.3.20'
    # username = 'root'
    # pwd = '123456'

    def __init__(self):
        # self.pool = {}
        pass

    # def getInstance(self, dbname):
    #     name = threading.current_thread().name
    #     if name not in self.pool:
    #         conn = pymysql.connect(self.ip, self.username, self.pwd, dbname)
    #         self.pool[name] = conn
    #     return self.pool[name]

    def showDB(self):
        # db = self.getInstance('allen_mix')
        db = pool.getResource()
        print("current occupied conn:", pool.busySize)
        cursor = db.cursor()
        start_time = time.time()
        try:
            cursor.execute("""select * from allen_mix.Websites;""")
        except pymysql.DatabaseError as error:
            total_time = int((time.time() - start_time) * 1000)
            self._locust_environment.events.request_failure.fire(request_type="PyMySQL",
                                                                 name='Query',
                                                                 response_time=total_time,
                                                                 exception=error,
                                                                 response_length=0)
            raise error
        else:
            print(cursor.fetchone())
            total_time = int((time.time() - start_time) * 1000)
            self._locust_environment.events.request_success.fire(request_type="PyMySQL",
                                                                 name='Query',
                                                                 response_time=total_time,
                                                                 response_length=0)
        finally:
            # self.pool.release()
            pass


class MyLocust(User):

    abstract = True

    def __init__(self, *args, **kwargs):
        super(MyLocust, self).__init__(*args, **kwargs)
        # self.client = MyClient()
        self.client = MySqlClient()
        self.client._locust_environment = self.environment


class UserBehavior(TaskSet):

    def on_stop(self):
        # currentThread = threading.current_thread().getName()
        # self.client.pool[currentThread].close()
        # logging.info("{} --> connection closed".format(currentThread))
        # pool.close()
        pool.release()
        print("current occupied conn:", pool.busySize)
        pass

    # @task
    def show(self):
        self.client.showTime()
        print(self.client.collection)

    @task
    def testDB(self):
        self.client.showDB()


class MyTasks(MyLocust):
    wait_time = between(3, 5)
    tasks = [UserBehavior]


if __name__ == '__main__':
    os.system('locust -f locust-demo.py')












