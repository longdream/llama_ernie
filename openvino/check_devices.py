#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查 OpenVINO 可用设备"""

import openvino as ov

core = ov.Core()
devices = core.available_devices

print("=" * 60)
print("OpenVINO 可用设备")
print("=" * 60)

for device in devices:
    try:
        name = core.get_property(device, "FULL_DEVICE_NAME")
        print(f"  {device}: {name}")
    except Exception as e:
        print(f"  {device}: (无法获取名称: {e})")

print("=" * 60)

