import os
import glob
import sys
import re

import psycopg2

from config import user_db, passwd_db


sql = """\
select * from tpl_client_raw_bills where cust_id = 631 limit 10;"""

params = {
    'host': 'revpgdb01.revintel.net',
    'database': 'tpliq_tracker_db',
    'user': user_db,
    'password': passwd_db
}
con = psycopg2.connect(**params)
cur = con.cursor()
cur.execute(sql)


cols = (x[0] for x in cur.description)


file_path = r'L:\pending_rejected_case_managers\report_delimit.csv'

with open(file_path, 'w') as fw:
    header = '|'.join(i for i in cols)
    print(header, file=fw)
    for line in cur:
        l0 = '|'.join(str(i) for i in line)
        print(l0, file=fw)


#----
# convert line endings from to linux LR to windows CFLR
#----

LINIX_LINE_ENDING = b'\n'    # b as btye sequence mapped not a string
WINDOWS_LINE_ENDING = b'\r\n'

with open(file_path, 'rb') as open_file:
    content = open_file.read()
# print(content)

content = content.replace(LINIX_LINE_ENDING, WINDOWS_LINE_ENDING)
with open(file_path, 'wb') as open_file:
    open_file.write(content)

