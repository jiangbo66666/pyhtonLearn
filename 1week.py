from getNum import getNum

name = "张三"
age = 18
money = 100.01
female = True
print(f"他叫{name},今年{age}岁,有{money}元存款,是{'女' if female else '男'}性")

score = 90

disc = "及格" if score >= 60 else "不及格"
if score >= 90:
    print("优秀")
elif score >= 80:
    print("良好")
elif score >= 60:
    print("及格")
else:
    print("不及格")

for i in range(10): print(i)

listA = [1,9,9,6,"oda"]

for i in listA: print(i)

obj = {"name":"张三","age":18,"money":100.01,"female":True}

print(obj["name"])

# 函数
def add(a, b):
    return a+b
print(add(1,2))

def greet(name , word = "你好"):
    print(f"{name}说,{word}")

greet("张三")

# 异常处理
getNum()


