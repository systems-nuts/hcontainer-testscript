#!/usr/bin/python3

import subprocess
import time
import os
import signal
import invoke
import fabric
from threading import Thread
from fabric import Connection

REQSIZE=300
MACHINE1="root@192.168.10.22"
MACHINE2="root@192.168.10.23"
RBENCH="/usr/local/bin/redis-benchmark" 
RBENCH_PARAMS=["-t", "get", "-d", str(REQSIZE)]
TIMEOUT_SEC=10
TMP_DIR="/tmp/hcbench"
FAKE_LAT_DIR="~/hcontainer-experiment"

# Launch one instance of the redis benchmark on server with command line
# params (array of strings)
# Return:
# - the execution time in sec if everything went well
# - 0 if the server is not reachable
# - a negative number in case of other error
def launch_bench(server, port, params):
    cmd = [RBENCH]
    cmd += params
    cmd += ["-h", server]
    cmd += ["-p", str(port)]
    retcode = 0
    res = 0.0
    print("Launching...")
    print("CMD: ",cmd)
    done = 0
    start = time.time()
    while not done:
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            retcode = e.returncode
            if(retcode != 1):
                print("Cannot run redis-benchmark on server " + server + ": " +
                        str(e))
                return -1.0
            else:
                if(time.time() - start >= TIMEOUT_SEC):
                    print("Error: client timed out")
                    return -1.0
                continue
        res = time.time() - start
        done = 1

    return res

def init():
    out = ""
    c1 = Connection(MACHINE1)
    c2 = Connection(MACHINE2)
    connections = [c1, c2]
    print("c1",c1,"c2",c2)
    # Cleanup
    for c in connections:
        try:
            res = c.run("sudo rm -rf " + TMP_DIR + "; sudo pkill redis-server",
                    hide=True)
        except invoke.exceptions.UnexpectedExit as e:
            pass

    # Copy files on fist machine
    cmd = ['scp','-r', os.getcwd() + '/redis-het', MACHINE1 + ":" + TMP_DIR]
    try:
        subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
            print("Cannot scp in temp folder on " + MACHINE1 + ": " + str(e))

    # Just create dir on second and kill existing instances
    print("copy success")
    c2.run("mkdir " + TMP_DIR + "; chmod 755 " + TMP_DIR)
    
    # Now launch redis
    cmd = ["ssh", MACHINE1, "sleep .5; cd " + TMP_DIR + "; ./redis-server --protected-mode no"]
    subprocess.Popen(cmd)

    time.sleep(10)

    # Get the PID
    out = c1.run("pidof redis-server", hide=True)
    print("out: ", out)
    time.sleep(3)
    for c in connections:
        c.close()
    return int(out.stdout)

def migrate(pid):
    out = ""
    c1 = Connection(MACHINE1)

    # Dump the state
    c1.run("cd " + TMP_DIR + "; mkdir x86_64")
    c1.run("cd " + TMP_DIR + "; sudo criu-het dump --arch x86-64 -j -t " + str(pid) + " --tcp-established",
            pty=True)
    c1.run("cd " + TMP_DIR + "; mv *.img x86_64/")
    # Copy it to the destination
    c1.run("cd " + TMP_DIR + "; cp redis-server_x86-64 redis-server")
    c1.run("cd " + TMP_DIR + "; scp -r x86_64 redis-server* " + MACHINE2 + ":"
            + TMP_DIR)

    # Now resume on destination
    # TODO use fabric?
    cmd = ["ssh", "-tt", MACHINE2, "cd " + TMP_DIR +
            "/x86_64; sudo criu-het restore -j --tcp-established"]
    process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)

    process.wait()

    c1.close()
    return

def exit_gracefully(arg1, arg2):
    print("Exit signal received, cleaning stuff")

    c1 = Connection(MACHINE1)
    c2 = Connection(MACHINE2)

    for c in [c1, c2]:
        try:
            c.run("sudo pkill redis-server; sudo pkill fake-latency.py")
        except invoke.exceptions.UnexpectedExit as e:
            pass

    exit(0)

# Should be called by a thread
def fake_latency(server, iface, period, lat, reverse):
    cmd = ("cd " + FAKE_LAT_DIR + " ; sudo ./fake-latency.py -i " + iface +
        " -p " + str(period) + " -l " + str(lat))
    if(reverse):
        cmd += " -r " + str(reverse)
    popen_cmd = ["ssh", "-tt", server, cmd]

    process = subprocess.Popen(popen_cmd, stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)

    process.wait()
    return

print("START")
# Catch signals to exit gracefully
signal.signal(signal.SIGINT, exit_gracefully)
signal.signal(signal.SIGTERM, exit_gracefully)
print("SIGNAL OVER")
pid = init()
print("PID: ",pid)

# Make a serie of SET to populate
launch_bench("localhost", 6379,
        ["set" if x == "get" else x for x in RBENCH_PARAMS])


print("Init done, starting experiment")
fl_process1 = Thread(target=fake_latency, args=[MACHINE1, "eth0", 100, 1000, 0])
fl_process1.start()
fl_process2 = Thread(target=fake_latency, args=[MACHINE2, "eth0", 100, 1000, 10000])
fl_process2.start()

init_ts = time.time()
migrated = 0
girl="localhost"
while True:
    ret = launch_bench(girl, 6379, RBENCH_PARAMS)
    print(str(time.time() - init_ts) + ": " + str(ret))
    if migrated == 0 and time.time() - init_ts > 20:
        process = Thread(target=migrate, args=[pid])
        process.start()
        # Sleep 2 sec before launching the next bench, for now we don't support
        # migrating in the middle of the benchmark ...
        time.sleep(2)
        migrated = 1
        girl="192.168.10.23"

    # Exit when done
    if(time.time() - init_ts > 1010):
        os.kill(os.getpid(), signal.SIGTERM)
