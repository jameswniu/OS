import os, sys
import re
import json

import psycopg2
import paramiko
import pandas as pd

from pprint import pprint
from datetime import datetime
from pytz import timezone

from paramiko import SSHClient
from scp import SCPClient

from config import user_db, passwd_db, user_linux, passwd_linux
from integration__data_transformation_from_database_old_employee_2_to_new_json_format import main_converter


def convert_xlsx_csv(file):
    df = pd.read_excel(file)
    df = df[df.columns.drop(list(df.filter(regex='Unnamed:')))]  # drop unnamed columns
    # print(df)

    new_file = file.replace('.xlsx', '.csv')
    df.to_csv(new_file, index=False)
    print(f'converted to... {new_file}\n')

    return new_file


def check_dx_desciption(dicy):
    if 'dx_code_desc' not in dicy:
        sql_dx = f"select string_agg(code || '|' || info, '@') from tpl_icd_codes where code = ANY(regexp_split_to_array('{dicy['diagnoses']}', ','));"

        with con:
            cur = con.cursor()
            cur.execute(sql_dx)

        desc = list(cur)[0][0]    # first record first column

        try:
            print('{} : "diagnoses": "{}" (added "dx_code_desc": "{}...")'.format(dicy['vx_pm_sk'], dicy['diagnoses'], desc[:60]))
        except:
            print('{} : no dx_code_desc | "diagnoses": "{}"'.format(dicy['vx_pm_sk'], dicy['diagnoses']))
        else:
            dicy['dx_code_desc'] = desc


params = {
    'host': 'revpgdb01.revintel.net',
    'database': 'tpliq_tracker_db',
    'user': user_db,
    'password': passwd_db}
con = psycopg2.connect(**params)


os.chdir(r'L:\claim_drop_request')


#----
# extract from input case manager spreadsheet after VERIFY
#----
file = 'raw_data__manual_input_from_employee_to_insert_database_and_bill_out.xlsx'  # 1 SPECIFY

if '.xlsx' in file:
    new_file = convert_xlsx_csv(file)
else:
    new_file = file


jar = {}
head_d = {}
cust_d = {}
acct_d = {}
t = 0
p = 0
q = 0

with open(new_file, 'r') as fr:
    head = fr.readline().strip()
    head_l = head.split(',')

    for i in range(len(head_l)):
        head_d[head_l[i]] = i
    # print(head_d)    # dict of headers: index

    for line in fr:
        line = line.strip()

        tmp = line.split(',')

        cust_id = tmp[head_d['cust_id']]
        cust_d[cust_id] = 1
        acct = tmp[head_d['pat_acct']].replace('"', '')
        acct_d[f"'{acct}'"] = 1

        keycsv = '{}|{}'.format(cust_id, acct)

        try:
            inst_prof = tmp[head_d['claim_type']]
        except:
            print('Create claim_type col and search DB')
            sys.exit()
        else:
            if inst_prof == '837P':
                p += 1
            else:
                q += 1

        dol = tmp[head_d['accident_date']]
        accidstate = tmp[head_d['accident_state']]

        carrier = tmp[head_d['carrier_name']].upper()
        claimnum = tmp[head_d['carrier_claim_number']].upper().replace('-', '').replace('"', '')
        policynum = tmp[head_d['insured_policy_number']].upper().replace('-', '').replace('"', '')

        fax = ''.join(re.findall(r'\d', tmp[head_d['adjuster_fax_number']]))

        raw = tmp[head_d['claim_party (fp or tp)']].upper()

        if raw == 'FP':
            fptp = 'FP'

            lob = 'AUTO (PERSONAL)'
        elif raw == 'WC':
            fptp = 'TP'

            lob = 'WORKERS COMP & EMPLOYERS LIABILITY'
        else:
            fptp = 'TP'

            lob = 'AUTO (PERSONAL)'

        jar[keycsv] = '{}|{}|{}|{}|{}|{}|{}|{}'.format(dol, accidstate, carrier, claimnum, policynum, fax, fptp, lob)

        t += 1

    accts = ', '.join(acct_d)
    custs = ', '.join(cust_d)


#----
# dump JSON
#----
sql = f"""select 'client' tbl, claim_content final_content from tpl_client_raw_bills where cust_id in ({custs}) and pat_acct in ({accts})
union all
select 'raw' tbl, new_content final_content from public.tpl_raw_bills a where cust_id in ({custs}) and pat_acct in ({accts})
and not exists (select 1 from tpl_client_raw_bills b where a.cust_id = b.cust_id and a.pat_acct = b.pat_acct);"""

with con:
    cur = con.cursor()
    cur.execute(sql)


#----
# write new bills
#----
Ymd = datetime.now(tz=timezone('America/New_York')).strftime('%Y%m%d')
md = Ymd[4:]

if p > 0:
    fw0 = open('zzp_{}_fax.json'.format(md), 'w')
if q > 0:
    fw1 = open('zzi_{}_fax.json'.format(md), 'w')


mail = """\
2492770, 3476139
2492771, 3476140
2492772, 3476141
2492773, 3476142
2492774, 3476143
2492775, 3476144
2492776, 3476145
2492777, 3476146
2492778, 3476147
2492779, 3476148
2492780, 3476149
2492781, 3476150
2492782, 3476151
2492783, 3476152
2492784, 3476153
2492785, 3476154
2492786, 3476155
2492787, 3476156
2492788, 3476157
2492789, 3476158
2492790, 3476159
2492791, 3476160
2492792, 3476161"""    # 2 SPECIFY by supervisor
pm_sk_l = [
]
src_sk_l = [
]

for pair in mail.split('\n'):
    sep = ','

    pm_sk = pair.split(f'{sep}')[0].strip()
    src_sk = pair.split(f'{sep}')[1].strip()

    pm_sk_l.append(pm_sk)
    src_sk_l.append(src_sk)


i, j = 0, 0
l, m = 0, 0

print(f"""\
fp_tp
cust_id|pat_acct|vx_pm_sk|vx_src_sk\
|vx_carrier_claim_number|vx_carrier_policy_number|vx_carrier_name\
|vx_date_of_loss|vx_accident_state|vx_carrier_city\
|vx_carrier_state|vx_carrier_zip|vx_carrier_lob\
|vx_claim_type|vx_carrier_insured_first_name|vx_carrier_insured_last_name\
|send_fax_number
vx_pm_sk : dx_code_desc

lockbox - roswellmailbox"""    # print header
)
print('-' * 150)

for row in cur:
    tbl = row[0]
    dicy0 = row[1]

    if 'client' in tbl:
        dicy = dicy0
    elif 'raw' in tbl:
        dicy = main_converter(dicy0)

    keydicy = '{}|{}'.format(dicy['cust_id'], dicy['pat_acct'])
    # print(keydicy)

    for keycsv in jar:
        if keydicy == keycsv:
            jarlist = jar[keycsv].split('|')
            # print(jarlist)

            dicy['vx_pm_sk'] = str(pm_sk_l[i])
            i += 1

            dicy['vx_src_sk'] = str(src_sk_l[j])
            j += 1

            dicy['vx_carrier_claim_number'] = jarlist[3]
            dicy['vx_carrier_policy_number'] = jarlist[4]
            dicy['vx_carrier_name'] = jarlist[2]
            date0 = datetime.strptime(jarlist[0], '%Y-%m-%d')
            date1 = datetime.strftime(date0, '%Y%m%d')
            dicy['vx_date_of_loss'] = date1
            dicy['vx_accident_state'] = jarlist[1]
            dicy['vx_carrier_city'] = ''
            dicy['vx_carrier_state'] = ''
            dicy['vx_carrier_zip'] = ''
            dicy['vx_claim_type'] = jarlist[6]
            dicy['vx_carrier_lob'] = jarlist[7]
            dicy['vx_carrier_insured_first_name'] = ''
            dicy['vx_carrier_insured_last_name'] = ''
            dicy['send_fax_number'] = jarlist[5]

            print(f"""{dicy['claim_type']}
{keydicy}|{dicy['vx_pm_sk']}|{dicy['vx_src_sk']}\
|{dicy['vx_carrier_claim_number']}|{dicy['vx_carrier_policy_number']}|{dicy['vx_carrier_name']}\
|{dicy['vx_date_of_loss']}|{dicy['vx_accident_state']}|{dicy['vx_carrier_city']}\
|{dicy['vx_carrier_state']}|{dicy['vx_carrier_zip']}|{dicy['vx_carrier_lob']}\
|{dicy['vx_claim_type']}|{dicy['vx_carrier_insured_first_name']}|{dicy['vx_carrier_insured_last_name']}\
|{dicy['send_fax_number']}"""    # print details
                  )

            if dicy['cust_id'] == '321' or dicy['cust_id'] == '405':
                dicy['roswell_mailbox'] = 'Medlytix;10800 Alpharetta Hwy,Suite 208 #773;Roswell, GA 30076-1417'
                dicy['pay_to_addr1'] = 'PO BOX 740937'
                dicy['pay_to_addr2'] = ''
                dicy['pay_to_city'] = 'ATLANTA'
                dicy['pay_to_state'] = 'GA'
                dicy['pay_to_zip'] = '303740937'
            if dicy['cust_id'] == '538' or dicy['cust_id'] == '734':
                dicy['pay_to_addr1'] = 'PO BOX 740011'
                dicy['pay_to_addr2'] = ''
                dicy['pay_to_city'] = 'ATLANTA'
                dicy['pay_to_state'] = 'GA'
                dicy['pay_to_zip'] = '303740011'
            if dicy['cust_id'] == '631':
                dicy['roswell_mailbox'] = 'Medlytix;PO BOX 746744;Atlanta, GA 30374-6744'
                dicy['pay_to_addr1'] = 'PO BOX 746744'
                dicy['pay_to_addr2'] = ''
                dicy['pay_to_city'] = 'ATLANTA'
                dicy['pay_to_state'] = 'GA'
                dicy['pay_to_zip'] = '303746744'


            if dicy['claim_type'] == '837P' and p > 0:
                check_dx_desciption(dicy)    # fill in dx_code_desc

                try:    # print pay_to
                    print(f"""\n{dicy['pay_to_addr1']}, {dicy['pay_to_addr2']}, {dicy['pay_to_city']}, {dicy['pay_to_state']} {dicy['pay_to_zip']} - {dicy['roswell_mailbox']}""")
                except:
                    print(f"""\n{dicy['pay_to_addr1']}, {dicy['pay_to_addr2']}, {dicy['pay_to_city']}, {dicy['pay_to_state']} {dicy['pay_to_zip']} - """)

                print(json.dumps(dicy), file=fw0)

                l += 1
            elif dicy['claim_type'] == '837I' and q > 0:
                try:    # print pay_to
                    print(f"""\n{dicy['pay_to_addr1']}, {dicy['pay_to_addr2']}, {dicy['pay_to_city']}, {dicy['pay_to_state']} {dicy['pay_to_zip']} - {dicy['roswell_mailbox']}""")
                except:
                    print(f"""\n{dicy['pay_to_addr1']}, {dicy['pay_to_addr2']}, {dicy['pay_to_city']}, {dicy['pay_to_state']} {dicy['pay_to_zip']} - """)

                print(json.dumps(dicy), file=fw1)

                m += 1

            print('-' * 150)
            # print(json.dumps(dicy), file=fw0)
print(f'837P {l} | 837I {m} | total {l+m}/{t}')

if p > 0:
    fw0.close()
if q > 0:
    fw1.close()


#----
# transfer file to linux
#----
try:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.load_system_host_keys()
    ssh.connect(hostname='revproc01.revintel.net',
                username=user_linux,
                password=passwd_linux)

    # SCPCLient takes a paramiko transport as its only argument
    scp = SCPClient(ssh.get_transport())

    if os.path.exists('zzp_{}_fax.json'.format(md)):
        scp.put('zzp_{}_fax.json'.format(md), f'/home/james.niu@revintel.net/production/jsondump/groupp_{md}.json')

        print(f"""\nscp transport success...
/home/james.niu@revintel.net/production/jsondump/groupp_{md}.json""")

    if os.path.exists('zzi_{}_fax.json'.format(md)):
        scp.put('zzi_{}_fax.json'.format(md), f'/tmp/groupi_{md}.json')

        print(f"""\nscp transport success...
/home/james.niu@revintel.net/production/jsondump/groupi_{md}.json""")
except:
    print('\nconnection failed*')
