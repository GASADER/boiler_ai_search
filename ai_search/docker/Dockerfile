# ใช้ Python 3.11 บน Linux ARM64 (รองรับ ชิป Apple Silicon M1)
FROM python:3.11-slim

# ตั้งค่าโฟลเดอร์ทำงานภายใน Container
WORKDIR /app

# ติดตั้งระบบพื้นฐานที่จำเป็น
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt-get/lists/*

# คัดลอกและติดตั้ง Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# สร้างโฟลเดอร์จำกัดพื้นที่สำหรับเซฟไฟล์ของ Agent (Sandbox Workspace)
RUN mkdir -p /app/workspace

# คัดลอกโค้ดทั้งหมดเข้ามาใน Container
COPY . .

# สั่งรันสคริปต์หลักเมื่อเปิด Container
CMD ["python", "main.py"]