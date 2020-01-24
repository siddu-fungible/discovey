from lib.host.linux import Linux, NoLogger

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

linux_obj = Linux(host_ip="qa-ubuntu-02", ssh_username="auto_admin", ssh_password="fun123", use_paramiko=False)
linux_obj.scp(source_file_path="/tmp/a.sh", target_ip="qa-ubuntu-02", target_username="auto_admin", target_password="fun123", target_file_path="/tmp/1234.txt", sudo=True, sudo_password="fun123")

#linux_obj = Linux(host_ip="10.1.20.67", ssh_username="root", ssh_password="fun123", use_paramiko=False)
# linux_obj.logger = NoLogger()
output = linux_obj.command(command="grep ATTENTION /root/parser.log", include_last_line=True)

o = linux_obj.command("date")
o = linux_obj.command("ls -l /jj")

linux_obj.exit_status()

