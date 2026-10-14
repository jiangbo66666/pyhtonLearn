from getNum import getNum
import requests

getNum()

class dog:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    def bark(self):
        print(f"{self.name}在汪汪叫")

dog1 = dog("旺财", 1)
dog1.bark()

response = requests.get("https://www.baidu.com")
print(response.status_code)
print(response.text)