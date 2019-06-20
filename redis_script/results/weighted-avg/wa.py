#!/usr/bin/python3



for name in ["mig.csv", "atom.csv", "potato.csv"]:
    last_ts = 0.0
    wsum = 0.0
    tsum = 0.0
    with open(name) as f:
        while(True):
            line = f.readline()
            if not line:
                break

            ts = float(line.split(",")[0])
            th = float(line.split(",")[1])

            t = ts - last_ts
            wsum += t*th
            tsum += t

            last_ts = ts

        print(name + ": " + str(wsum/tsum))
