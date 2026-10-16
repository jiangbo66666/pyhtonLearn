"""
==============================================================================
文件: functioncalling.py
主题: 原生 function calling（函数调用）+ 流式输出的完整实现 —— 逐行注释版
==============================================================================

【写在最前面: 这个脚本到底在干什么？】
  用户打一句话 → 发给大模型 → 如果模型判断需要用工具, 它就"点名"要调哪个工具
  → 我们在本机真的把这个函数执行一遍 → 把执行结果再发回给模型
  → 模型根据这个结果, 用人类的语言回答问题 → 全程边生成边打印, 不用等整段写完

【和同目录 modelrequest.py 的区别】
  modelrequest.py: 在提示词里"求"模型按 JSON 格式回答, 形如 {"result": 内容, "tool": 工具名},
                   然后自己用 json.loads 解析。
                   缺点: 正文文字和 JSON 的符号混在同一股数据流里, 没法直接逐字打印给用户。
  本文件: 改用 API 官方支持的 tools 参数。正文走 content 通道, 工具调用走 tool_calls 通道,
          两条通道从协议层就是分开的。所以正文拿到就能直接打印, 一行 JSON 解析都不需要。

【一次完整请求的时间线】
  1. 用户输入 → 追加进 messages 列表（messages 就是"聊天历史记录", 每轮都发给模型）
  2. 调 client.chat.completions.create(..., stream=True, tools=TOOLS) 发起请求
  3. 服务端把回复切成很多小块(chunk)陆续推回来, 我们用 for 循环一块一块地处理
  4. 若模型决定用工具: 块里会带 tool_calls 信息（而且是"分片"传的, 需要自己拼起来）
  5. 我们在本机执行 getNum(), 拿到数字
  6. 把"我调用了 getNum, 结果是 13"作为一条 role="tool" 的消息塞回 messages
  7. 再请求一次模型: 这次它不再调工具, 直接把最终答复以正文形式流式输出, 本轮结束
  8. 把整个 messages 存进 json 文件, 下次启动还能接着聊（这就是"记忆"）

【Python 语法速查（本文件用到的所有基础语法）】
  · 变量:        名字 = 值               例如 text = ""（Python 不用事先声明类型）
  · 函数:        def 函数名(参数):        下面缩进的部分就是函数体; return 后面是返回值
  · 缩进:        Python 用缩进（一般 4 个空格）表示"哪个代码属于哪一块", 同级必须对齐
  · 字典 dict:   {"键": 值, "键2": 值2}   取值方式: 字典["键"]
  · 列表 list:   [元素1, 元素2]           取值方式: 列表[下标], 下标从 0 开始
  · 判断真假:    ""(空字符串)、[](空列表)、{}(空字典)、None 在 if 里都算"假", 其它基本都算"真"
  · f"字符串":   格式化字符串, 花括号 {} 里的内容会被替换成变量的实际值
  · +=:          累加, text += "a" 等价于 text = text + "a"
  · None:        Python 中表示"什么都没有"的特殊值, 类似其他语言的 null / nil
  · 注释:        # 后面的一整行都是给人看的说明, Python 会完全忽略它
"""

# =============================================================================
# 第 1 部分: 导入需要的模块
# 说明: "import 模块" = 把别人写好的工具箱拿进来用, 避免自己造轮子
# =============================================================================

import os          # os: 操作系统相关工具。本文件只用它一个功能: 读环境变量 os.environ.get(...)
import json        # json: 专门处理 JSON 文本的工具。负责"JSON 字符串 ↔ Python 字典"互转
from pathlib import Path   # Path: 路径工具类。比手动拼字符串更安全, 还能判断文件是否存在

from dotenv import load_dotenv   # load_dotenv: 把 .env 文件里的配置读进环境变量
from openai import (             # openai 官方 SDK（软件开发工具包）: 帮我们封装 HTTP 请求
    OpenAI,                      # OpenAI: 客户端类, 用它创建 client 对象来发请求
    APIConnectionError, APITimeoutError, RateLimitError,   # 下面是 SDK 可能抛出的各种异常类
    AuthenticationError, APIStatusError, APIError,         # 异常 = "出错时抛出来的信号", 能被捕获处理
)

from tool import getNum   # 从同目录的 tool.py 里导入 getNum 函数（就是那个返回 1~100 随机数的函数）

# =============================================================================
# 第 2 部分: 准备工作（路径、配置、客户端、工具定义、系统提示词）
# =============================================================================

# __file__ 是 Python 内置变量, 表示"当前这个 .py 文件自身的路径"
# .resolve() 把它转成绝对路径; .parent 取它所在的目录（也就是 05bigModel 文件夹）
BASE_DIR = Path(__file__).resolve().parent

# 把 .env 里的配置（API Key、base_url 等）加载到环境变量里, 不然 os.environ 读不到它们
# .env 文件位置: h:\pyhtonLearn\.env
load_dotenv()

# 本脚本使用独立的记忆文件, 避免污染 modelrequest.py 用的 memory.json
MEMORY_FILE = BASE_DIR / 'memory_functioncalling.json'
# 注: Path 对象支持用 / 拼接路径（不是除法）, 效果等于 BASE_DIR + "\memory_functioncalling.json"

# 创建 OpenAI 客户端对象。它是我们和大模型服务通信的"电话机"
# 括号里全部是"关键字参数"（名字=值 的形式）, 顺序无所谓
client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),      # 从环境变量取密钥（.env 里配的）
    base_url=os.environ.get('openai_api_base_url'),  # 接口地址, 指向实际提供服务的服务器
    timeout=30.0,     # 单次请求最多等 30 秒, 超时抛 APITimeoutError
    max_retries=2,    # 连接失败/限流/5xx 报错时, SDK 自动重试 2 次
)

# -----------------------------------------------------------------------------
# TOOLS: 工具说明书。告诉模型"你有一个名叫 getNum 的工具可用, 它不需要参数"
# 关键点: 这里是"结构化定义", 交给 API 解析, 而不是写在提示词里让模型自己照着格式写
# 数据结构: 最外层是列表 [ ], 里面每个元素是一个字典 { }, 描述一个工具
# -----------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",              # 固定写法: 工具类型是"函数"
        "function": {                    # 这个键下面描述函数本身
            "name": "getNum",            # 函数名: 模型点名时用的就是这个名字, 必须和 run_tool 里判断的一致
            "description": "生成一个 1-100 之间的随机数，需要随机数时调用",  # 给模型看的用途说明, 写得越清楚它越会用对
            "parameters": {              # 参数说明（按 JSON Schema 语法写, 由 API 校验）
                "type": "object",        # 固定写法: 参数整体是一个对象（即字典）
                "properties": {},        # 具体有哪些参数。getNum 不用参数, 所以这里是空的字典
                "required": [],          # 哪些参数是必填的。空的列表 = 没有必填参数
            },
        },
    },
]

# -----------------------------------------------------------------------------
# SYSTEM_PROMPT: 系统提示词, 相当于给模型的"人设 + 规矩", 放在 messages 的最前面
# 相邻的两个字符串字面量会自动首尾拼接成一个字符串（这是 Python 的特性）
# -----------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "你是一个前端开发，名叫啊三，今年30岁，来自中国，拥有丰富的工作经验，现在正在学习python。"
    "当用户需要随机数时，直接调用 getNum 工具获取，不要自己编造数字。"
)

# =============================================================================
# 第 3 部分: 函数定义区（def 开头）
# 说明: 把一段逻辑"打包"成函数, 好处是能重复调用, 而且主流程读起来更清楚
# =============================================================================


def load_memory():
    """
    功能: 读取记忆文件, 把上次对话的历史记录加载回来。
    返回值: 一个字典, 形如 {"messages": [ ...历史消息... ]}
    """
    # MEMORY_FILE.exists() 判断文件是否存在, 返回 True / False
    if MEMORY_FILE.exists():
        try:
            # with open(...) as f: 是打开文件的标准写法
            # 好处: 离开这段缩进后文件会自动关闭, 不用手动写 f.close()
            # 'r' 表示只读模式; encoding='utf-8' 指定编码, 否则中文会乱码
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                # json.load(f): 把文件里的 JSON 文本读成 Python 的字典/列表, 然后作为结果返回
                return json.load(f)
        except json.JSONDecodeError:
            # 如果文件内容被写坏了（不是合法 JSON）, 上面那行会抛异常
            # 这里捕获它, 打印一句提示, 然后走到函数最下面用默认值兜底, 避免程序直接崩溃
            print(f"{MEMORY_FILE.name} 内容损坏，已重置记忆")

    # 走到这里有两种情况: 文件不存在, 或者文件损坏被上面捕获了
    # 返回一个"全新的记忆": 只有一条 system 消息（也就是人设 + 工具规矩）
    return {"messages": [{"role": "system", "content": SYSTEM_PROMPT}]}


def save_memory(memory):
    """
    功能: 把记忆保存到文件, 下次启动程序时能接着上次聊。
    参数 memory: 要保存的字典（也就是当前完整的对话历史）
    返回值: 没有（这种函数只管做事, 不给结果, 所以不用 return）
    """
    # 'w' 表示写入模式: 文件不存在就新建, 已存在则整个覆盖
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        # json.dump: 把 Python 字典写成 JSON 文本存进文件
        # ensure_ascii=False → 中文直接写中文, 不写成 \uXXXX 转义码（否则文件没法看）
        # indent=4          → 每层缩进 4 空格, 纯粹为了文件好看、方便人阅读
        json.dump(memory, f, ensure_ascii=False, indent=4)


def stream_once(memory):
    """
    功能: 发一次流式请求。正文边收边打印; 工具调用信息分片收齐后整理好一并返回。
    参数 memory: 当前的对话历史字典
    返回值: 一个"元组"(text, calls), 也就是两个值打包一起返回:
              text  → 模型这次输出的正文文字（字符串）
              calls → 模型请求调用的工具列表（列表）; 如果是空列表 [], 说明这轮是纯文本回复
    """
    # 发起请求。create() 是 SDK 提供的方法, 负责把参数打包成 HTTP 请求发给服务器
    # 关键参数说明:
    #   messages         → 完整对话历史, 模型靠它"记住"上文
    #   stream=True      → 流式: 返回的不是完整结果, 而是一个"迭代器", 可以一块块地取
    #   tools=TOOLS      → 把工具说明书交给 API, 由 API 规整地告诉模型有哪些工具
    #   reasoning_effort → 思考投入程度（low = 省时间省钱）
    #   extra_body       → SDK 没有专门参数时, 用这个字典透传服务商的私有参数（这里是开启思考）
    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=memory["messages"],
        stream=True,
        reasoning_effort="low",
        extra_body={"thinking": {"type": "enabled"}},
        tools=TOOLS,
    )

    text = ""              # 准备一个空字符串, 用来一点点攒出完整正文
    finish_reason = None   # 结束原因, 先给 None（表示还不知道）; 服务端最后会告诉我们
    # 工具调用在流里是按"分片"下发的（比如函数名分 2 块、参数分 3 块）
    # 所以用字典来归组: 键 = 第几个工具调用(index), 值 = 这个调用的信息
    tool_calls = {}

    # for chunk in response: 迭代器写法。
    # 每循环一次就向服务器要下一小块数据; 所有块取完（收到结束标记）后循环自动结束。
    # 这一步是"阻塞"的: 网络没给下一块, 程序就在这里等着 —— 这正是流式能边收边显示的原因
    for chunk in response:
        # chunk.choices 是个列表, 正常情况下有 1 个元素。
        # 但如果开了用量统计, 最后会多出一个只带统计信息、没有 choices 的块。
        # 空列表 [] 在 if 里算"假", 所以 not chunk.choices 为真时直接跳过它, 防止下面取值报错
        if not chunk.choices:
            continue        # continue = 跳过本次循环剩下的代码, 直接进入下一次循环

        choice = chunk.choices[0]   # 取下标 0, 也就是第一个（通常也是唯一一个）候选结果

        # finish_reason 只有"最后一块"才不是 None。它的可能取值:
        #   "stop"       → 模型正常说完了
        #   "tool_calls" → 模型要去调用工具
        #   "length"     → 达到 max_tokens 上限被截断
        if choice.finish_reason:
            finish_reason = choice.finish_reason

        delta = choice.delta   # delta 是"增量"对象: 这次新增的那一点点内容

        # ---- 通道 1: 正文 ----
        # if delta.content: 当内容是空字符串或 None 时算"假", 直接跳过（不是每块都有正文）
        # （另外, 带思考的模型会把思考过程放在 delta.reasoning_content 里, 本脚本不展示）
        if delta.content:
            text += delta.content                  # 把这一小块正文追加到总文本后面
            # 立刻打印这一小块。两个关键参数:
            #   end=""     → 打印后不换行（print 默认结尾会加换行, 这里改成空, 才能连成一行）
            #   flush=True → 立刻把内容推送到屏幕, 不攒在缓存里。没有它, 你就会"憋"到最后才一次显示
            print(delta.content, end="", flush=True)

        # ---- 通道 2: 工具调用（和正文完全分开, 互不干扰）----
        # delta.tool_calls 大多数块是 None。`X or []` 是 Python 的常用写法:
        #   如果 X 是 None 或空, 就取右边的 [] 来代替, 这样 for 循环就不会因为 None 报错
        for tc in (delta.tool_calls or []):
            # setdefault 是字典的方法: 键已存在就返回已有的值; 键不存在就先写入第二个参数再返回
            # 作用: 第一次遇到第 index 个工具调用时, 先建一个空壳把三个字段占好位
            slot = tool_calls.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
            if tc.id:                       # id 一般只在第一片里出现, 有就记下来
                slot["id"] = tc.id
            if tc.function and tc.function.name:
                slot["name"] += tc.function.name          # 函数名拼起来（+= 是累加拼接）
            if tc.function and tc.function.arguments:
                slot["arguments"] += tc.function.arguments   # 参数字符串拼起来: 必须收完才能解析

    if text:
        print()   # 只输出一个换行。作用: 让后面打印的工具日志从新的一行开始, 不与正文黏在一起

    if finish_reason == "length":
        print("[提示] 达到 max_tokens 被截断，回复不完整")

    # 把上面拼好的 tool_calls 字典, 整理成标准格式的列表。
    # 下面这段是"列表推导式": 一种一句话生成列表的简写, 等价于先 calls = [] 再 for 循环往里 append
    #   sorted(tool_calls.items()) → 字典的 items() 给出 (键, 值) 配对, sorted 按键(index)从小到大排序,
    #                                 保证多个工具调用的先后顺序稳定
    #   for i, slot in ...         → 把每对 (键, 值) 拆成两个变量 i 和 slot（这叫"解包"）
    #   slot["id"] or f"call_{i}"  → 万一个别服务商没给 id, 就用 call_0 / call_1 自己补一个, 保证有唯一标识
    calls = [
        {
            "id": slot["id"] or f"call_{i}",
            "type": "function",
            "function": {"name": slot["name"], "arguments": slot["arguments"]},
        }
        for i, slot in sorted(tool_calls.items())
    ]
    return text, calls   # 把两个值打包返回, 调用方用 text, calls = stream_once(...) 一次接住


def run_tool(call):
    """
    功能: 真正在本地执行一个工具调用, 并返回"给模型看的结果文字"。
    参数 call: 一个工具调用字典, 形如 {"id":..., "type":"function", "function":{"name":..., "arguments":...}}
    返回值: 字符串。字符串形式的工具执行结果（因为回灌给模型时, content 必须是字符串）
    """
    name = call["function"]["name"]     # 一层一层往下取字典: call["function"] 再 ["name"]
    # arguments 是模型给的参数字符串（JSON 文本）。`or "{}"` 兜底: 万一它是空字符串, 用 "{}" 代替（合法空 JSON）
    raw_args = call["function"]["arguments"] or "{}"

    try:
        # json.loads: 把 JSON 字符串解析成 Python 字典。getNum 没参数, 所以这里得到的是空字典 {}
        args = json.loads(raw_args)
    except json.JSONDecodeError:
        # 模型偶尔会给出不合法的 JSON。纪律: 不能因此让整个程序崩溃, 而是把错误信息当结果回灌,
        # 让模型下一轮自己意识到问题并改正
        print(f"[工具] {name} 参数解析失败: {raw_args}")
        return f"参数不是合法 JSON: {raw_args}"

    if name == "getNum":            # 按名字分发到具体的 Python 函数
        value = getNum()            # 调用 tool.py 里那个函数, 真的生成一个随机数
        print(f"[工具] getNum({args}) -> {value}")   # 打印日志, 让你看到"模型确实请求调用了工具"
        return str(value)           # str() 把数字转成字符串, 才能作为消息内容发回去

    # 模型点名了一个我们没实现的工具（比如它记错了工具名）
    print(f"[工具] 未知工具: {name}")
    return f"没有名为 {name} 的工具"

# =============================================================================
# 第 4 部分: 主流程（程序从这里开始真正执行）
# 注意: 上面的 def 只是"定义", 定义时不执行; 走到这里才开始按顺序执行代码
# =============================================================================

# 调用 load_memory() 函数取得记忆, 存进变量 memoryJson（沿用 modelrequest.py 的命名习惯）
# memoryJson 里最终长这样: {"messages": [ {"role": "system", ...}, {"role": "user", ...}, ... ]}
memoryJson = load_memory()

# while True: 无限循环, 直到遇到 break 才跳出（程序靠这个实现"一直聊天直到输入 exit"）
while True:
    # input(...) 会暂停程序, 等你从键盘敲一行并回车; 返回值就是你敲的那行文字
    # 前面的 \n 是为了先空一行, 让提示更醒目
    userMessage = input("\n请输入:")
    print(f"用户输入:{userMessage}")     # f-string: {userMessage} 会被替换成你刚输入的内容
    if userMessage == "exit":
        break                            # 跳出外层 while 循环 → 往后执行到文件末尾, 程序结束

    # ---- 把用户这句话追加进历史 ----
    turn_start = len(memoryJson["messages"])   # len() 取列表长度。记下本轮的起始下标, 便于出错时整体回滚
    # append: 列表方法, 往列表末尾加一个元素。这里加的是一个字典, role="user" 表示"这是用户说的话"
    memoryJson["messages"].append({"role": "user", "content": userMessage})

    # 内层 while: 模型可能连续多次调用工具（比如先查数再算), 所以反复请求,
    # 直到它某一次不再请求工具（也就是 calls 为空）才结束本轮对话
    while True:
        # try / except / else 是 Python 的错误处理结构:
        #   try    → 试着执行, 出错就跳到对应的 except
        #   except → 捕获指定类型的异常, 程序不中断, 而是执行这里的补救代码
        #   else   → 只有 try 里"完全没有出错"时才执行的分支
        try:
            # 调用上面定义的函数。函数返回两个值, 这里用逗号一次接住（顺序不能错）
            text, calls = stream_once(memoryJson)
        # 下面每个 except 处理一种具体错误, 顺序是从具体到笼统
        except APITimeoutError:
            print("请求超时，稍后重试")
        except APIConnectionError:
            print("网络连接失败，检查网络或 base_url")
        except RateLimitError:
            print("触发限流，请降速重试")
        except AuthenticationError:
            print("API Key 无效或过期，检查 .env")
            # 切片删除: memoryJson["messages"][turn_start:] 取出"从本轮起点到末尾"这一段, del 把它整段删掉
            # 目的是把本轮添加的 user 消息以及可能的半截工具消息全部撤销, 不让坏数据污染历史
            del memoryJson["messages"][turn_start:]
            # raise 主动抛出一个异常。SystemExit 是 Python 内置的"结束程序"信号, 效果就是终止脚本
            raise SystemExit
        except APIStatusError as e:
            # as e: 把捕获到的异常对象起名叫 e, 这样就能读它的属性, 比如 e.status_code（HTTP 状态码）
            print(f"接口报错 {e.status_code} : {e.message} ")
        except APIError as e:
            print(f"其他错误: {e} ")
        else:   # ---- 到这里说明请求成功, 没有发生任何异常 ----
            if not calls:
                # calls 是空列表 [] → 模型这次没请求调工具, 那就是普通的文字回复, 本轮到此结束
                # 把模型的回答以 role="assistant" 存进历史（记住"我说过什么")
                memoryJson["messages"].append({"role": "assistant", "content": text})
                break       # 跳出内层 while, 回到最上面等用户输入下一句

            # ---- 有工具调用: 先把"模型的这次回复"记进历史 ----
            # 注意: 这条 assistant 消息除了 content, 还要带上 tool_calls,
            # 因为按 API 规定, 后面那条 role="tool" 的结果必须"回应"某一次具体的工具调用请求
            memoryJson["messages"].append({
                "role": "assistant",
                "content": text or None,   # text 为空字符串时用 None 代替（模型只请求调工具、一句话没说就属于这种情况）
                "tool_calls": calls,       # 原样存下工具调用列表
            })
            # ---- 逐个执行工具, 把结果回灌给模型 ----
            for call in calls:
                result = run_tool(call)    # 真正执行（这里是本地跑 getNum()）
                # role="tool" 是专用的"工具结果"角色; tool_call_id 指明这是对哪一次调用的回应, 一一对应
                memoryJson["messages"].append({
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": result,
                })
            # continue 表示"跳过本次循环剩下代码, 直接开始下一次内层循环" → 于是带着工具结果再请求一次模型
            # 这一次模型通常就会直接用正文回答"随机数是 13", 不再请求工具, 然后走上面的 break 结束本轮
            continue

        # 代码能执行到这里, 说明 try 里抛异常了且被某个 except 接住了（成功路径都在 else 里, 不会到这儿）
        # 统一做回滚处理: 删掉本轮产生的所有消息, 保持历史干净, 然后结束本轮, 让用户重新输入
        del memoryJson["messages"][turn_start:]
        break       # 跳出内层 while, 回到最上面等用户输入

    # 本轮对话结束（无论是正常结束, 还是出错回滚后结束), 把最新的历史写进文件保存
    save_memory(memoryJson)
