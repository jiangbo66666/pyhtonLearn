import json
import requests
import sys
from pathlib import Path

# 模块搜索路径 sys.path 只会自动包含"脚本所在目录"，不含父目录
# 所以先把项目根目录（本文件的上一级）加进去，才能 import 到根目录下的 getNum.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from getNum import getNum

# 相对路径的参照点是"运行时的工作目录"，不是脚本所在目录
# 所以先用 __file__ 拿到脚本自己的目录，再拼接文件路径，换任何地方运行都不会找不到
BASE_DIR = Path(__file__).resolve().parent

print(BASE_DIR)

def openBillSystem():
    billData = {}

    with open(BASE_DIR / "record.json", "r" , encoding="utf-8") as f:
        billData = json.load(f)
        print(billData)

    choice = input("欢迎来到账本系统，请输入 \n 1 记一笔 / 2 查看全部 / 3 退出 \n")

    if choice == "1":
        print("请输入金额:")
        billMoney = getNum()
        billRemark = input("请输入备注:")
        billData["bills"].append({"billMoney": billMoney, "billRemark": billRemark})
        billData["totalMoney"] += billMoney
        # 打开文件，写入数据，关闭文件，f是文件对象
        with open(BASE_DIR / "record.json", "wt" , encoding="utf-8" , newline= "\n") as f:
            json.dump(billData, f, ensure_ascii=False, indent=4)
        input("按任意键继续")
        openBillSystem()
    elif choice == "2":
        print("查看全部")
        for bill in billData["bills"]:
            print(f"{bill['billMoney']}元,{bill['billRemark']}")
        print(f"当前余额为{billData['totalMoney']}元")
        input("按任意键继续")
        openBillSystem()
    else:
        print("退出")

openBillSystem()