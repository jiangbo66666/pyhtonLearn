# 异常处理小工具：从 1week.py 抽离出来，供其他文件 import 复用
def getNum():
    try:
        num = input("请输入一个数字:")
        num = int(num)
        print(num)
        return num
    except ValueError:
        return getNum()
    except ZeroDivisionError:
        print("除数不能为0")
        return getNum()
