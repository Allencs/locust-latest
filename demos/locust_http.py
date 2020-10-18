import os
from locust import task, HttpUser, TaskSet, between, SequentialTaskSet, events
from locust.contrib.fasthttp import FastHttpUser
from locust.exception import RescheduleTask, InterruptTaskSet


class MyTasks(TaskSet):

    # @task
    def task1(self):
        print("this is first task...")

    @task
    class MyApi(SequentialTaskSet):

        token = None

        @task
        def token(self):
            # response = self.client.get("/pftest/myApi/token")
            # if response is not None:
            #     print("RescheduleTask()")
            #     raise RescheduleTask()
            with self.client.get("/", catch_response=True) as response:
                if response.text is None:
                    response.failure("Got wrong response")

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


class MyUser(FastHttpUser):
    wait_time = between(0, 0)
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

