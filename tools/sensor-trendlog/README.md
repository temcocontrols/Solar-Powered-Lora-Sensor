# RA-08 串口传感器 Trendlog

## 启动
在此目录双击 `start.cmd`，保持启动窗口开启，用桌面 Chrome / Edge 打开 http://localhost:8765 。无需安装前端依赖，全部资源在本地，不向服务器上传采集数据。需要 Python 3。

连接 USB 串口后点击“连接串口”并选择网关。默认 115200、8N1、无流控（固件 main.c 的配置）。若连接失败，请关闭占用同一端口的串口助手。串口访问需要浏览器授权。不要直接双击 HTML 或通过局域网 HTTP 地址使用串口功能。

## 协议
固件依据：`projects/ASR6601CB-EVAL/examples/lora/lora_myself_net/components/lora_driver/lora_driver.c` 中网关 AT 转发。

`AT+SENSOR=<8位十六进制UID>,<温度×100>,<湿度×100>,<电容电压mV>,<CO₂ ppm>,<TVOC ppb>,<照度lux>,<RSSI dBm>,<SNR dB>`

示例 `AT+SENSOR=B7180A12,2332,5627,65,390,0,13,-94,8` 表示 23.32°C、56.27%RH、65mV、390ppm、0ppb、13lux、-94dBm、8dB。电压按固件原始单位保留，65mV 不转换成 6.5V。0 值保留；协议没有提供有效性标记，无法判断 0 是真实读数还是未启用传感器。

串口以 CRLF / LF / CR 分帧，支持分包和一包多行。忽略普通调试日志，格式错误的 SENSOR 行不入库。没有换行的末行在断开时处理。

## 使用与保存
- 左侧选择节点，卡片显示最新值；趋势可切换全部八种指标和时间范围。表格显示最近 100 条，图表和导出使用完整记录。
- IndexedDB 自动保存历史，刷新后恢复；需始终使用同一浏览器、配置文件及 `localhost:8765` 地址。无痕模式、清理站点数据会影响保存。建议定期导出。
- CSV 导出全部节点，包含 ISO 接收时间、转换后的数值、原始消息；JSON 备份可重新导入并按时间+原始行去重。导入保留原时间。
- PNG 保存当前节点、指标和范围的图表。
- 记录时间来自电脑接收时间，并非设备采样时间。样例按钮会插入真实持久记录（模拟时间），正式采集前可清空。
- 关闭页面后停止采集。读取异常时会持续恢复读取；设备掉线后每 2 秒尝试重新打开原设备，直到手动点击 Disconnect。设备离线或电脑休眠期间无法接收数据；若系统将设备识别为新的串口，需要手动断开并重新选择。长期无人值守建议使用独立后台采集服务。
- 无自动删除历史策略；当前版本将历史读入内存，趋势按图表像素绘制最小/最大包络，统计和导出仍使用全部记录。大量连续采集请分期备份清空。

## 校验
运行 `node protocol.test.cjs` 校验解析、范围和串口分包处理。实际串口采集需要连接设备验证。

## Silent-read recovery

The Idle recovery setting defaults to 2 minutes. If no serial bytes arrive within that interval, the pending reader is cancelled and the original port is closed and reopened automatically. Set this longer than the gateway's normal quiet interval, or choose Disabled for intentionally silent devices. A quiet device is indistinguishable from a stalled read using received bytes alone.

The Serial diagnostic line shows received bytes, the last byte time, and the last valid record time. Bytes increasing without new records indicates incoming data that does not parse as valid SENSOR frames; inspect Raw messages. All labels remain in English.

The chart refreshes at most once per second during acquisition and draws a min/max envelope for large histories. Full data is retained for statistics and exports. Parser errors are reported separately and no longer interrupt serial reading.

Additional regression tests: `node serial-session.test.cjs` and `node recovery.test.cjs`.
