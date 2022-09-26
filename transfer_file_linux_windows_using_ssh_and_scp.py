import paramiko

from paramiko import SSHClient
from scp import SCPClient

from config import user_linux, passwd_linux


#----
# create test file
#----
f = open("getext.txt","w+")

for i in range(10):
     f.write("This is line %d\r\n" % (i+1))

f.close()

#----
# transfer to (and from) linux server through SSH shell and SCP protocol
#----

ssh = SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.load_system_host_keys()
ssh.connect(hostname='revanalyst01.revintel.net',
            username=user_linux,
            password=passwd_linux)

# SCPCLient takes a paramiko transport as its only argument
scp = SCPClient(ssh.get_transport())

scp.put('D:\\Users\\james.niu\PycharmProjects\\Reports\\getext.txt', '/home/james.niu@revintel.net')
scp.get('/home/james.niu@revintel.net/bbb.py', 'L:\pending_rejected_case_managers')

scp.put('L:\Auto_Opportunity_Analysis\Check_Accts_Production_CP.sql', 'L:\pending_rejected_case_managers')