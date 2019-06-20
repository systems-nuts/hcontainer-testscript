#!/usr/bin/python3

import time, subprocess

TARGET="potato"
RBENCH="./redis/prefix/bin/redis-benchmark"
RBENCH_PARAMS=["-t", "get", "-d", "300"]
TIMEOUT_SEC = 10

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
                print(out)
                return -1.0
            else:
                if(time.time() - start >= TIMEOUT_SEC):
                    print("Error: client timed out")
                    return -1.0
                continue
        res = time.time() - start
        done = 1

    return res

# Make a serie of SET to populate
launch_bench(TARGET, 5000,
        ["set" if x == "get" else x for x in RBENCH_PARAMS])

print("Init done, starting experiment")

init_ts = time.time()
while True:
    ret = launch_bench(TARGET, 6379, RBENCH_PARAMS)
    print(str(time.time() - init_ts) + ": " + str(ret))
