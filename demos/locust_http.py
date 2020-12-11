import os
from locust import task, HttpUser, TaskSet, between, SequentialTaskSet, events
from locust.contrib.fasthttp import FastHttpUser
from locust.exception import RescheduleTask, InterruptTaskSet


class MyTasks(TaskSet):

    # @task
    def task1(self):
        print("this is first task...")

    """
    使用task装饰器，标记任务方法
    1、任务可以是一个方法，也可以是一个类（方法集合）
    2. 如果是任务类，必须继承TaskSet或者SequentialTaskSet（有序任务类）
    3.任务类可以嵌套
    """
    @task
    class MyApi(SequentialTaskSet):

        token = None

        @task
        def token(self):
            with self.client.get("/pftest/myApi/token", catch_response=True) as response:
                if response.text is None:
                    response.failure("Got wrong response")
                    # raise RescheduleTask()

        # @task
        def personInfo(self):
            reqBody = {"username": "GoodBoy", "pw": "root123"}
            headers = {"Behavior": "PerformanceTest",
                       "Position": "IT",
                       "access-token": self.token}
            response = self.client.post("/pftest/myApi/personInfo", json=reqBody, headers=headers)
            try:
                response.json()['Position'] == 'PerformanceTestEngineer'
            except Exception:
                print("InterruptTaskSet()")
                raise InterruptTaskSet(reschedule=True)

    # @task
    def task3(self):
        print("this is third task...")


class MyUser(HttpUser):
    """
    - 将方法传入locust执行类
    - 此处可设置每次请求间隔时间
    """
    wait_time = between(0, 0)
    # 执行类中的tasks属性，接受任务类，需传入一个列表
    tasks = [MyTasks]


# class MyUser(HttpUser):
#     wait_time = between(0, 0)
#     tasks = [MyTasks]


# @events.test_start.add_listener
def on_test_start(**kwargs):
    print("A new test is starting")


# @events.test_stop.add_listener
def on_test_stop(**kwargs):
    print("A new test is ending")


# if __name__ == '__main__':
#     os.system('locust -f locust_http.py --host="http://192.168.3.20:8080"')

