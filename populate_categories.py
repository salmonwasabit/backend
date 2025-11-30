#!/usr/bin/env python3
import json

import requests

# Categories to add
categories = [
    {
        "name": "บุหรี่ไฟฟ้าทิ้ง",
        "description": "Starter Kit และ Cartridge หลากหลายรสชาติ เหมาะสำหรับผู้เริ่มต้น",
    },
    {"name": "ระบบพอต", "description": "Pod ระบบปิดพร้อมรสชาติพรีเมียมและการใช้งานที่สะดวก"},
    {"name": "โมดส์", "description": "อุปกรณ์สูบไอระดับพรีเมียมพร้อมคุณสมบัติขั้นสูง"},
    {"name": "น้ำยาสูบ", "description": "น้ำยาสูบไอหลากหลายรสชาติและความเข้มข้น"},
    {"name": "อุปกรณ์เสริม", "description": "อุปกรณ์และอะไหล่สำหรับการสูบไอ"},
    {"name": "ธีมเกม", "description": "สินค้าการสูบไอธีมเกมและตัวละครสุดพิเศษ"},
    {"name": "อื่นๆ", "description": "สินค้าอื่นๆที่เกี่ยวข้องกับการสูบไอ"},
]

base_url = "http://localhost:8000"

print("Adding categories to database...")

for category in categories:
    try:
        response = requests.post(
            f"{base_url}/api/categories",
            json=category,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            print(f"✅ Added category: {category['name']}")
        else:
            print(
                f"❌ Failed to add {category['name']}: {response.status_code} - {response.text}"
            )

    except Exception as e:
        print(f"❌ Error adding {category['name']}: {e}")

print("\nChecking categories...")
try:
    response = requests.get(f"{base_url}/api/categories")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {len(data)} categories in database")
        for cat in data:
            print(f"  - {cat['name']}")
    else:
        print(f"❌ Failed to fetch categories: {response.status_code}")
except Exception as e:
    print(f"❌ Error fetching categories: {e}")
