import httpx, asyncio


async def test1():
    await asyncio.sleep(1)
    print("test1")
    return "test1"

async def test2():
    await asyncio.sleep(1)
    print("test2")
    return "test2"

async def test3():
    await asyncio.sleep(1)
    print("test3")
    return "test3"
# async def main():
#     # 方式一：直接传协程对象，gather 内部自动包装成 Task 并发调度
#     results = await asyncio.gather(test1(), test2())
#     print(results)  # ['test1', 'test2']，约 1 秒完成

#     # 方式二：已有 Task 时解包传入
#     tasks = [asyncio.create_task(test1()), asyncio.create_task(test2())]
#     results = await asyncio.gather(*tasks)
#     print(results)
# # 走 asyncio.run 才能执行
# # asyncio.run(test1())
# # asyncio.run(test2())

# # 注意：gather 必须在事件循环内被 await，最外层用 asyncio.run 启动
# # asyncio.run(main())
# asyncio.run(test1())

async def main():
    # 方式一：直接传协程对象，gather 内部自动包装成 Task 并发调度
    await asyncio.gather(test1(), test2())
    # 方式二：已有 Task 时解包传入
    results = [asyncio.create_task(test1()), asyncio.create_task(test2())]
    # 上面两种方式等价
    await asyncio.gather(*results)
    print("main")
    


# asyncio.run(main())


async def maintest():
    results = [asyncio.create_task(test1()), asyncio.create_task(test2())]
    await asyncio.sleep(1)
    await asyncio.gather(*results)
    print("maintest")

async def maintest2():
    results = [asyncio.create_task(test1()), asyncio.create_task(test2())]
    # 顺序执行
    # await test3()
    # await asyncio.sleep(1)
    # 可以但是 不一定能跑完 且总共需要1s
    # asyncio.create_task(test3())
    # 这个函数只要有一个await 就要等待这个执行完成,才能走下面, await 上方创建好的调度 然后在下面gather 的 不会受到影响
    await asyncio.create_task(test3())
    # gather 只是在收集结果，如果没有创建 Task 任务，就不会并发调度，所以需要等待上面的 await asyncio.sleep(1) 完成，才能并发调度 asyncio.create_task(test1()) 才是实质的创建调度 执行
    await asyncio.gather(*results)
    print("maintest")

# asyncio.run(maintest())
asyncio.run(maintest2())