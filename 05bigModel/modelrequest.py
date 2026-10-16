import os
from dotenv import load_dotenv
from openai import (
    OpenAI,
    APIConnectionError, APITimeoutError, RateLimitError,
    AuthenticationError, APIStatusError, APIError,
)
import json
from pathlib import Path

from tool import getNum

BASE_DIR = Path(__file__).resolve().parent
# 把 .env 里的配置加载到环境变量里，不然 os.environ 读不到
load_dotenv()

client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url=os.environ.get('openai_api_base_url'),
    timeout=30.0,     # 单次请求最多等 30 秒
    max_retries=2,    # 连接失败/限流/5xx 自动重试
)

memoryJson = {}

def getMemory():
    with open(BASE_DIR / 'memory.json', 'r', encoding='utf-8') as f:
        memory = json.load(f)
        return memory

memoryJson = getMemory()
while True:
    userMessage = input("\n请输入:")
    print(f"用户输入:{userMessage}")
    if userMessage == "exit":
      break
    memoryJson["messages"].append({"role": "user", "content": userMessage})
    # try :
    #     response = client.chat.completions.create(
    #         model= "deepseek-flash" ,
    #         messages=memoryJson[ "messages" ],
    #         stream= False ,
    #         reasoning_effort= "low" ,
    #         extra_body={ "thinking" : { "type" : "enabled" }},
    #     ) 
    try :
        response = client.chat.completions.create(
            model= "deepseek-flash" ,
            messages=memoryJson[ "messages" ],
            stream= True ,
            reasoning_effort= "low" ,
            extra_body={ "thinking" : { "type" : "enabled" }},
        ) 
    except APITimeoutError: print ( "请求超时，稍后重试" ) 
    except APIConnectionError: print ( "网络连接失败，检查网络或 base_url" ) 
    except RateLimitError: print ( "触发限流，请降速重试" ) 
    except AuthenticationError: 
      print ( "API Key 无效或过期，检查 .env" ) 
      break 
    except APIStatusError as e: 
      print ( f"接口报错 {e.status_code} : {e.message} " ) 
    except APIError as e: 
      print ( f"其他错误: {e} " ) 
    else :
        # 空回复不算异常，在成功分支里单独判断
        # if not response.choices or not response.choices[0].message.content:
        #     print ( "模型返回空回复" ) 
        #     memoryJson[ "messages" ].pop() 
        #     continue 
        # reply = response.choices[0].message.content 
        reply = ""
        streamReply = ""
        for chunk in response:
            reply = chunk.choices[0].delta.content
            if(reply):
                streamReply += reply
                print(reply, end="", flush=True)
        # print ( f"模型回复: {reply} " )
        # 流式记忆存储
        # 从流中回复中提取结果
        try:
            result = json.loads(streamReply)
        except json.JSONDecodeError:
            # 模型没按 JSON 格式返回时，打印原文便于排查，并回滚本轮 user 消息，避免污染历史
            print(f"模型返回非 JSON 格式: {streamReply}")
            memoryJson["messages"].pop()
            continue
        print(result)
        # 从流中回复中提取工具调用
        
        # 调用工具函数
        if result.get("tool") == "getNum":
            print(result.get("result", ""))
            print(getNum())
        else:
            # tool 为 none 或缺失：属于普通对话，直接输出模型说话内容
            print(result.get("result", "模型没有返回可解析的内容"))
        memoryJson[ "messages" ].append({ "role" : "assistant" , "content" : streamReply}) 
        with open (BASE_DIR / 'memory.json' , 'w' , encoding= 'utf-8' ) as f:
            json.dump(memoryJson, f, ensure_ascii= False , indent= 4 ) 
        continue # 成功：跳过下面的回滚 # 能走到这里 = 本轮失败，删掉刚加的 user 消息，避免污染历史 
    memoryJson[ "messages" ].pop()




# print(response.choices[0].message.content)
# print(response.to_json())


