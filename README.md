# Risk Management Dashboard

แดชบอร์ดสำหรับดึงไฟล์ **Excel + รูปใน PowerPoint** จาก **SharePoint ไซต์ IT Audit / Risk Management** แล้วประมวลผลก่อนเผยแพร่บน **GitHub Pages** ผู้ที่มีลิงก์ต้องใส่รหัสผ่านก่อนเข้า และมีปุ่ม **รีเฟรชข้อมูล** เพื่ออัปเดตชุดข้อมูลใหม่

> หน้าเว็บบน GitHub Pages เป็นไฟล์นิ่ง รหัสผ่านช่วยกันผู้ที่ไม่ได้ตั้งใจเปิดลิงก์ ไม่ใช่ระบบ login ระดับองค์กร หากข้อมูลเป็นความลับสูง ควรใช้ repo ส่วนตัว หรือชั้นป้องกันอย่าง Cloudflare Access เพิ่ม

## ทำงานอย่างไร

1. ไฟล์อยู่ที่ SharePoint: [IT Audit / Risk Management](https://singerthaicoth.sharepoint.com/sites/ITAudit/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2FITAudit%2FShared%20Documents%2FRisk%20Management)
2. สคริปต์ Python ดึงไฟล์ → อ่านทะเบียนความเสี่ยง → ดึงรูปจากสไลด์ → เขียน `docs/data/dashboard.json`
3. GitHub Pages เสิร์ฟโฟลเดอร์ `docs/`
4. ปุ่มรีเฟรช
   - **บนเครื่อง:** ประมวลผลทันทีผ่าน `http://127.0.0.1:8080/api/refresh`
   - **บนเว็บ:** โหลดข้อมูลล่าสุดที่เผยแพร่แล้ว และถ้าใส่ GitHub token จะสั่ง workflow ให้ดึงไฟล์จาก SharePoint ใหม่

## เปิดบนเครื่องนี้

ต้องมี Python 3.10+ (เครื่องนี้มีแล้ว)

```bat
start.bat
```

หรือ

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r pipeline\requirements.txt
.\.venv\Scripts\python pipeline\run.py
.\.venv\Scripts\python pipeline\serve.py 8080
```

เปิด [http://127.0.0.1:8080](http://127.0.0.1:8080)

รหัสผ่านเริ่มต้น: **`Risk2026`**

อย่าเปิด `docs/index.html` ตรง ๆ จากไฟล์ เพราะเบราว์เซอร์จะบล็อกการโหลด JSON

## คอลัมน์ Excel ที่รองรับ

ใช้ชื่อไทยหรืออังกฤษได้ สคริปต์จับหัวคอลัมน์ให้อัตโนมัติ

| ฟิลด์ | ชื่อที่รองรับ |
| --- | --- |
| รหัส | รหัสความเสี่ยง, ID, Risk ID |
| หัวข้อ | หัวข้อ, ความเสี่ยง, Title |
| หมวดหมู่ | หมวดหมู่, Category |
| ความน่าจะเป็น | ความน่าจะเป็น, Likelihood (1–5) |
| ผลกระทบ | ผลกระทบ, Impact (1–5) |
| ผู้รับผิดชอบ | ผู้รับผิดชอบ, Owner |
| สถานะ | สถานะ, Status |
| มาตรการ | มาตรการ, Mitigation |
| แนวโน้ม | แนวโน้ม, Trend |

คะแนน = ความน่าจะเป็น × ผลกระทบ ถ้าไม่มีคอลัมน์คะแนนในไฟล์

## เปลี่ยนรหัสผ่าน

```powershell
.\.venv\Scripts\python pipeline\set_password.py รหัสใหม่ของคุณ
```

จากนั้น commit ไฟล์ `docs/js/config.js` แล้ว push

บน GitHub ให้ตั้ง Actions secret ชื่อ `DASHBOARD_PASSWORD` เป็นรหัสเดียวกัน เพื่อให้ workflow รีเฟรชเขียน hash ให้ตรงกัน

## Deploy บน GitHub

1. สร้าง repo ใหม่ แล้ว push โปรเจกต์นี้
2. GitHub → **Settings → Pages**
   - Source: **Deploy from a branch**
   - Branch: `master` / โฟลเดอร์ `/docs`
3. รอ 1–2 นาที แล้วเปิด `https://<user>.github.io/<repo>/`
4. ตั้งค่า **Settings → Secrets and variables → Actions**

| Secret | จำเป็นเมื่อ |
| --- | --- |
| `DASHBOARD_PASSWORD` | ต้องการให้ workflow เขียนรหัสผ่านให้ |
| `ONEDRIVE_TENANT_ID` | `756171ea-7618-4380-8d31-17505ead61dd` |
| `ONEDRIVE_CLIENT_ID` | Azure app สำหรับอ่าน SharePoint |
| `ONEDRIVE_CLIENT_SECRET` | สำหรับ GitHub Actions (แอปแบบ application permission) |
| `SHAREPOINT_URL` | ลิงก์โฟลเดอร์ Risk Management |
| `ALFRESCO_*` | ถ้าใช้ Alfresco แทน SharePoint |
| `GITHUB_REPO` | ไม่ต้องใส่ — workflow ใส่ `github.repository` ให้ |

คัดลอก `.env.example` เป็น `.env` สำหรับรันบนเครื่อง

อย่า commit ไฟล์ `.env`

## เชื่อม SharePoint (IT Audit / Risk Management)

แหล่งข้อมูลที่ตั้งไว้แล้ว:

`https://singerthaicoth.sharepoint.com/sites/ITAudit` → **Shared Documents / Risk Management**

ทำอย่างใดอย่างหนึ่ง:

### วิธีที่ 1 — ซิงค์โฟลเดอร์ลงเครื่อง (เร็วสุด)

ใน File Explorer เปิด `OneDrive - Singer Thailand Public Company Limited\Internal Audit and Risk Management - Risk Management` แล้วคลิกขวา → **Always keep on this device**

พอไฟล์ Excel / PowerPoint ลงมา กดรีเฟรชบนแดชบอร์ดได้เลย ไม่ต้องสร้าง Azure app

### วิธีที่ 2 — ล็อกอินครั้งเดียวด้วยบัญชีบริษัท

1. [Azure Portal](https://portal.azure.com) → **Microsoft Entra ID** → **App registrations** → New registration
2. Delegated permissions: `Sites.Read.All`, `Files.Read.All`
3. เปิด **Allow public client flows**
4. ใส่ `ONEDRIVE_CLIENT_ID` ใน `.env`
5. รัน

```powershell
.\.venv\Scripts\python pipeline\connect_sharepoint.py
.\.venv\Scripts\python pipeline\run.py
```

### วิธีที่ 3 — GitHub Actions ดึงเองทุกวัน

ใช้ Application permissions: `Sites.Read.All`, `Files.Read.All` แล้วให้ IT กด **Grant admin consent** จากนั้นใส่ `ONEDRIVE_CLIENT_ID` + `ONEDRIVE_CLIENT_SECRET` เป็น GitHub Secrets

ถ้ายังดึง SharePoint ไม่ได้ ระบบจะใช้ไฟล์ใน `inbox/` หรือไฟล์ตัวอย่างใน `sample-data/`

## ปุ่มรีเฟรชบนเว็บสาธารณะ

GitHub Pages ไม่มีเซิร์ฟเวอร์ ประมวลผลไฟล์จริงทำใน GitHub Actions

- Workflow `Refresh dashboard data` รันทุกวันเวลา 02:00 น. (ไทย) และรันมือได้ที่แท็บ Actions
- จากแดชบอร์ด: ปุ่ม **ตั้งค่า** → วาง Fine-grained PAT ที่สิทธิ์ `actions: write` เฉพาะ repo นี้ → กดรีเฟรช จะยิง `repository_dispatch`
- Token เก็บใน `sessionStorage` ของเบราว์เซอร์นั้น ไม่ได้ถูก commit เข้า git

## โครงสร้างโปรเจกต์

```
inbox/                 วางไฟล์ Excel / PPTX ชั่วคราว
sample-data/           ไฟล์ตัวอย่าง
pipeline/              ดึงข้อมูล + ประมวลผล + เซิร์ฟเวอร์ท้องถิ่น
docs/                  เว็บที่ GitHub Pages เสิร์ฟ
  data/dashboard.json  ผลลัพธ์หลังประมวลผล
  data/images/         รูปที่ดึงจาก PowerPoint
```
