# pyhtonLearn

AI Agent 开发学习仓库（前端转 AI 应用方向，Python 零基础起步）。

## 配套文档

| 文档 | 作用 |
| --- | --- |
| [AI-Agent-学习路线.md](./AI-Agent-学习路线.md) | 讲"为什么这样学"：路线图、阶段目标、时间规划 |
| [AI-Agent-学习任务书.md](./AI-Agent-学习任务书.md) | 讲"每天具体做什么"：任务清单、新手指引、报错速查 |

## 环境说明

- 操作系统：Windows
- Python：3.14.3（本机实际解释器路径 `C:\Users\Admin\AppData\Local\Python\bin\python.exe`）
- 虚拟环境：项目根目录下的 `.venv`（已被 `.gitignore` 忽略，不提交）

> ⚠️ **本机特别注意**：直接输入 `python` 会命中 Windows 商店的"应用执行别名"存根
> （`...\WindowsApps\python.exe`），它**不是真正的解释器**，执行会返回 exit 9009。
> 因此本仓库统一使用 **`py` 启动器**（Windows 官方 Python Launcher）。

### 验证解释器

```powershell
py --version          # 应输出 Python 3.14.3
where.exe python      # 若首个结果在 WindowsApps 下，即为存根，勿用
```

## 虚拟环境使用

### 1. 创建（已完成，换机时重建用）

```powershell
py -m venv .venv
```

### 2. 激活（进入环境）

PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

激活成功后命令行前缀会出现 `(.venv)`。若首次提示"禁止运行脚本"，先执行一次：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

cmd：

```bat
.\.venv\Scripts\activate.bat
```

Git Bash / WSL：

```bash
source .venv/Scripts/activate
```

### 3. 退出环境

```powershell
deactivate
```

### 4. 不激活直接用（可选）

```powershell
.\.venv\Scripts\python.exe 1week.py
```

> 激活后 `python` / `pip` 会优先指向 `.venv\Scripts`，不受上面的商店存根影响。

## 依赖管理

```powershell
# 激活环境后
py -m pip install -r requirements.txt      # 安装依赖
py -m pip freeze > requirements.txt        # 导出依赖快照
```

## 运行示例脚本

```powershell
# 激活环境后
python 1week.py
```

## 目录结构

```
pyhtonLearn/
├── .venv/                    # 虚拟环境（git 忽略）
├── .gitignore                # Git 忽略规则
├── 1week.py                  # 第 1 周练习：变量/条件/循环/列表/字典/函数
├── AI-Agent-学习路线.md       # 学习路线总览
├── AI-Agent-学习任务书.md     # 每日实操任务书
└── README.md                 # 本文件
```

## 常见问题

**Q：输入 `python` 报 exit 9009 / 无任何输出？**
A：命中了商店别名存根。用 `py`，或把全路径写全，或在「设置 → 应用 → 高级应用设置 → 应用执行别名」中关闭 `python.exe`、`python3.exe`。

**Q：PowerShell 提示"无法加载文件 activate.ps1，因为在此系统上禁止运行脚本"？**
A：执行 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`（只需一次）。

**Q：`pip install` 很慢或失败？**
A：可临时换镜像源，例如 `py -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <包名>`。
