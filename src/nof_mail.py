import yagmail
import traceback
import psycopg2
from psycopg2.extras import DictCursor
from pprint import pprint
from datetime import date, timedelta
import sys

# Connect to your postgres DB
conn = psycopg2.connect(
    host="127.0.0.1",
    database="pnradmin",
    user="pnradmin",
    password="PnR#UBU3030",
    cursor_factory=DictCursor
)

# Open a cursor to perform database operations
cur = conn.cursor()

# Execute a query
cur.execute("SELECT * FROM dashboard_store ORDER BY id")

# Retrieve query results
licenses = cur.fetchall()

licenses_data = list()

for i in licenses:
    r = dict()
    r.update(i['data'])
    if i['data']["contract_start"] == "-" or i['data']["contract_end"] == "-": continue
    if date.fromisoformat(i['data']["contract_end"]) < date.today(): continue
    if (date.fromisoformat(i['data']["contract_end"]) - date.fromisoformat(i['data']["contract_start"])) > timedelta(days=360):
        if (date.fromisoformat(i['data']["contract_end"]) - date.today()) < timedelta(days=124):
            licenses_data.append(r)
    else:
        licenses_data.append(r)
licenses_data.sort(key=lambda r: date.fromisoformat(r["contract_end"]))
if not licenses_data: sys.exit()
try:
    RECEIVER = ['property@ubu.ac.th','mr.surakiat.ta.62@ubu.ac.th', 'thanet.si.62@ubu.ac.th']
    yag = yagmail.SMTP(user='propertyubuv.2@ubu.ac.th',password='Xypp9393')
    greet = '<h4>เรียนผู้ดูแลระบบ สำนักบริหารทรัพย์สินและสิทธิประโยชน์ มหาวิทยาลัยอุบลราชธานี</h4>'
    table = "<table><thead><tr><th>ที่</th><th>ชื่อกิจการ</th><th>ชื่อผู้ได้รับสิทธิ์</th><th>วันสิ้นสุดสัญญา</th></tr></thead><tbody>"
    for i, l in enumerate(licenses_data):
        table += f'<tr><td>{i+1}</td><td>{l["Type"]}</td><td>{l["License_name"]}</td><td>{l["contract_end"]}</td></tr>'
    table += "</tbody></table>"
    link = 'https://pcmo.ubu.ac.th'
    body = f'{greet}<br>{table}<br>เข้าจัดการสัญญาได้ที่ {link}<br><i>สำนักบริหารทรัพย์สินและสิทธิประโยชน์ มหาวิทยาลัยอุบลราชธานี</i>'
    yag.send(to=RECEIVER , subject='แจ้งเตือนสัญญาของผู้ประกอบการที่ใกล้สิ้นสุดสัญญา', contents=body)
except:
    traceback.print_exc()