# MANUS + Vive Tracker Raw JSONL Capture

这个说明只讲现在怎么用本仓库采集原始 MANUS skeleton + Vive Tracker combined JSON 数据。

## 采集流程

整体启动顺序是：

1. 启动 MANUS Core，并确认手套和 Vive Tracker 已经在 Core 里正常出数据。
2. 启动 Python 采集脚本 `capture_raw_jsonl.py`。
3. 启动/运行 C++ `SDKMinimalClient_Windows`。
4. C++ 通过 TCP 连接 Python，持续发送 combined JSON。
5. Python 把收到的每一帧原样保存成 JSONL。

## 需要编译的 C++ 工程

需要编译这个工程：

```text
SDKMinimalClient_Windows/SDKMinimalClient.vcxproj
```

不要单独编译 `SDKMinimalClient_socket.cpp`，因为工程文件里配置了 MANUS SDK 的 include、lib、dll 路径。

如果用 Visual Studio：

1. 打开 `SDKClient.sln`。
2. 选择项目 `SDKMinimalClient_Windows`。
3. 配置选择 `Release x64` 或 `Debug x64`。
4. Build 项目。

如果用命令行，并且当前终端能找到 `msbuild`：

```powershell
cd D:\research_history\first_one\research_code\manus_vivetracker_communication\MANUS_Core_2.4.0.1_SDK
msbuild SDKMinimalClient_Windows\SDKMinimalClient.vcxproj /p:Configuration=Release /p:Platform=x64
```

编译产物通常会在：

```text
Output/x64/Release/SDKMinimalClient_Windows.exe
```

或：

```text
Output/x64/Debug/SDKMinimalClient_Windows.exe
```

具体取决于你选择的配置。

## 启动 Python 采集端

先启动 Python，因为 C++ 客户端会主动连接 Python 的 TCP server。

```powershell
cd D:\research_history\first_one\research_code\manus_vivetracker_communication\MANUS_Core_2.4.0.1_SDK
python capture_raw_jsonl.py --out data/raw_frames.jsonl
```

常用参数：

```powershell
python capture_raw_jsonl.py --out data/raw_frames.jsonl --duration 30
```

表示从收到第一帧开始，采集 30 秒。

```powershell
python capture_raw_jsonl.py --out data/raw_frames.jsonl --max-frames 1000
```

表示采集 1000 帧后停止。

```powershell
python capture_raw_jsonl.py --host 127.0.0.1 --port 8888 --out data/raw_frames.jsonl --print-every 30
```

默认参数就是：

```text
host = 127.0.0.1
port = 8888
out = data/raw_frames.jsonl
flush = true
print-every = 30
```

`data/` 目录会自动创建。

## 启动 C++ 客户端

Python 采集端显示等待连接后，再运行编译出来的 C++ exe。

例如：

```powershell
cd D:\research_history\first_one\research_code\manus_vivetracker_communication\MANUS_Core_2.4.0.1_SDK
.\Output\x64\Release\SDKMinimalClient_Windows.exe
```

程序启动后会让你选择连接模式：

```text
[1] Core Integrated
[2] Core Local
[3] Core Remote
```

一般 MANUS Core 跑在本机时选：

```text
2
```

C++ 连接成功后，会把 combined JSON 发送给 Python。Python 会持续把原始帧保存到 `data/raw_frames.jsonl`。

## 停止采集

可以用这些方式停止：

- Python 端设置了 `--duration`，到时间自动停止。
- Python 端设置了 `--max-frames`，到帧数自动停止。
- 在 Python 终端按 `Ctrl+C`。
- 在 C++ 客户端按空格退出。

建议优先让 Python 正常退出，这样 JSONL 文件句柄会被关闭。

## 输出文件格式

输出文件是 JSONL：

- 每一行是一帧完整 JSON。
- Python 不会给帧补字段。
- Python 保存的是 C++ 发来的 raw combined JSON。
- 不会转换成 CSV。

一行大概长这样：

```json
{"timestamp":123456789,"frame":0,"combined_monotonic_ms":12345,"skeleton_publish_time":123,"skeleton_receive_monotonic_ms":12340,"skeleton_frame":null,"skeleton_callback_index":1,"tracker_publish_time":456,"tracker_receive_monotonic_ms":12342,"tracker_frame":null,"tracker_callback_index":1,"skeletons":[{"gloveId":"...","nodes":[{"id":0,"position":[0.0,0.0,0.0],"rotation":[0.0,0.0,0.0,1.0]}]}],"trackers":[{"id":0,"trackerId":"...","position":[0.0,0.0,0.0],"rotation":[0.0,0.0,0.0,1.0],"quality":2,"valid":true,"last_update_time":789}]}
```

重要字段含义：

- `timestamp`: combined JSON 生成时的 `system_clock` Unix epoch ms，保留旧语义。
- `frame`: combined JSON 成功发送计数。
- `combined_monotonic_ms`: combined JSON 生成时的 `steady_clock` ms。
- `skeleton_publish_time`: MANUS SDK `SkeletonStreamInfo.publishTime.time`，为 `0` 时输出 `null`。
- `tracker_publish_time`: MANUS SDK `TrackerStreamInfo.publishTime.time`，为 `0` 时输出 `null`。
- `skeleton_receive_monotonic_ms`: skeleton callback 到达 C++ 程序时的 `steady_clock` ms。
- `tracker_receive_monotonic_ms`: tracker callback 到达 C++ 程序时的 `steady_clock` ms。
- `skeleton_callback_index`: C++ 程序收到 skeleton callback 的自增计数。
- `tracker_callback_index`: C++ 程序收到 tracker callback 的自增计数。
- `skeleton_frame`: 当前 SDK 没有真实 skeleton frame id，所以输出 `null`。
- `tracker_frame`: 当前 SDK 没有真实 tracker frame id，所以输出 `null`。
- `trackers[*].last_update_time`: 每个 tracker 自己的 `TrackerData.lastUpdateTime.time`，为 `0` 时输出 `null`。

`combined_monotonic_ms`、`skeleton_receive_monotonic_ms`、`tracker_receive_monotonic_ms` 只能在同一次采集 session 内比较时间差，不要当 Unix 时间用，也不要跨文件比较绝对值。

## 检查采集文件

采集完成后运行：

```powershell
python inspect_raw_jsonl.py --path data/raw_frames.jsonl
```

它会输出：

```text
total lines
valid json lines
frames with skeletons
frames with trackers
frames with node 4
frames with node 9
frames with tracker position
frames with tracker valid=true
frames with combined_monotonic_ms
frames with skeleton_publish_time
frames with tracker_publish_time
frames with skeleton_receive_monotonic_ms
frames with tracker_receive_monotonic_ms
frames with skeleton_callback_index
frames with tracker_callback_index
frames where each tracker has last_update_time
```

如果时间字段可用，还会输出这些时间差的 min / mean / max：

```text
abs(skeleton_receive_monotonic_ms - tracker_receive_monotonic_ms)
combined_monotonic_ms - skeleton_receive_monotonic_ms
combined_monotonic_ms - tracker_receive_monotonic_ms
```

## 常见问题

如果 C++ 提示连不上 Python：

- 确认先启动了 `capture_raw_jsonl.py`。
- 确认 Python 端口是 `8888`。
- 确认没有其他程序占用 `8888`。

如果 Python 一直等不到连接：

- 确认运行的是新编译的 `SDKMinimalClient_Windows.exe`。
- 确认 C++ 和 Python 使用同一台机器或同一个 host/port。

如果 JSONL 里只有 `skeletons` 没有 `trackers`：

- 检查 MANUS Core 里 Vive Tracker 是否正常连接。
- 检查 C++ 日志里是否出现 `[TRACKER]`。

如果 JSONL 里时间字段是 `null`：

- `publishTime.time == 0` 或 `lastUpdateTime.time == 0` 时会输出 JSON `null`。
- receive monotonic 字段应该在对应 callback 到达后出现。

## 推荐最小命令

一个最小采集流程：

```powershell
cd D:\research_history\first_one\research_code\manus_vivetracker_communication\MANUS_Core_2.4.0.1_SDK
python capture_raw_jsonl.py --out data/raw_frames.jsonl --duration 30
```

然后另开一个终端运行：

```powershell
cd D:\research_history\first_one\research_code\manus_vivetracker_communication\MANUS_Core_2.4.0.1_SDK
.\Output\x64\Release\SDKMinimalClient_Windows.exe
```

采集结束后检查：

```powershell
python inspect_raw_jsonl.py --path data/raw_frames.jsonl
```
