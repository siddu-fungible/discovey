from lib.host.linux import Linux

'''
linux_obj = Linux(host_ip="10.1.20.67", ssh_username="root", ssh_password="fun123")
# linux_obj.enable_logs(enable=False)
o = linux_obj.command("date")
o = linux_obj.lsblk()
p = linux_obj.get_process_id("qemu-system-x86_6")
print(p)
result = linux_obj.command("docker ps -a")

print "RESULT:" + str(result)

o = linux_obj.command("docker inspect --format='{{.LogPath}}' johns")

o = linux_obj.get_process_id("init")
i = 0
'''


linux_obj = Linux(host_ip="10.1.20.67", ssh_username="jabraham", ssh_password="Fun!@#", use_paramiko=False)
o = linux_obj.command("ls -l")
o = linux_obj.command("date")
