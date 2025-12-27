#!/usr/bin/env python3

import re
import time
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import argparse

# Raw string avoids needing to escape backslashes
LOGFILE = r"C:\Program Files (x86)\Steam\steamapps\common\Bigscreen Beyond Driver\bin\log.txt"

# This function courtesy of Google AI
def follow(targetFile):
    """
    Generator function that tails a file like the 'tail -f' command.
    """
    targetFile.seek(0, os.SEEK_END)
    
    while True:
        line = targetFile.readline()
        if not line:
            time.sleep(1)
            continue
        yield line


def main(args):
    dtFormmat = r"%Y-%m-%d %H:%M:%S"

    dataSeconds = 0
    if args.lastHours:
        dataSeconds += args.lastHours * 3600
    if args.lastMinutes:
        dataSeconds += args.lastMinutes * 60
    if args.lastSeconds:
        dataSeconds += args.lastSeconds
    
    if dataSeconds > 0:
        if args.startTime or args.endTime:
            print("Error: --lastX arguments are not compatible with --startTime or --endTime.")
            return
        print(f"Showing last {dataSeconds} seconds of data.")
    elif args.startTime and args.endTime:
        print(f"Showing data from {datetime.strptime(args.startTime, dtFormmat)} to {datetime.strptime(args.endTime, dtFormmat)}.")
    elif args.startTime:
        print(f"Showing data from {datetime.strptime(args.startTime, dtFormmat)} to present.")
    elif args.endTime:
        print(f"Showing data from start to {datetime.strptime(args.endTime, dtFormmat)}.")
    else:
        print("Showing all data.")
    

    print("Opening and parsing log file, please wait...")
    with open(LOGFILE, "r") as lf:
        ti = []
        temps = []

        # First load all the existing data points
        for line in lf:
            # Only parse lines starting with YYYY-MM-DD string
            if re.match(r'^\d{4}-\d{2}-\d{2}', line):
                time = line.split(",")[0]
                timeDT = datetime.strptime(time, dtFormmat)
                ti.append(timeDT)

                temp = line.split(",")[2]
                temps.append(float(temp))

        #plt.plot(ti, temps)
        #plt.scatter(ti, temps)
        plt.xlabel("Time")
        plt.ylabel("Temperature (C)")
        plt.title("BSB Temperature over Time")
        animated_plot = plt.plot(ti, temps, 'bo')[0]

        if args.endTime:
            endTimeDT = datetime.strptime(args.endTime, dtFormmat)
            plt.xlim(right = endTimeDT + timedelta(seconds=100))
            if args.startTime:
                startTimeDT = datetime.strptime(args.startTime, dtFormmat)
                plt.xlim(left = startTimeDT - timedelta(seconds=100))
            plt.show()
            return
        
        # turn interactive mode on to enable real-time updating
        plt.ion() 

        if args.startTime:
            plt.xlim(left = datetime.strptime(args.startTime, dtFormmat) - timedelta(seconds=100))

        # Plot new data points as they are written to the log file
        for line in follow(lf):
            if re.match(r'^\d{4}-\d{2}-\d{2}', line):
                time = line.split(",")[0]
                thisTime = datetime.strptime(time, dtFormmat)
                ti.append(thisTime)

                temp = line.split(",")[2]
                temps.append(float(temp))
            
            recentTimestamp = ti[-1]
            plotTi = ti
            plotTemps = temps

            if dataSeconds > 0:
                for t in ti:
                    if (recentTimestamp - t).total_seconds() <= dataSeconds:
                        cutIndex = ti.index(t)
                        break
                plotTi = ti[cutIndex:]
                plotTemps = temps[cutIndex:]
            
            elif args.startTime:
                startTimeDT = datetime.strptime(args.startTime, dtFormmat)
                for t in plotTi:
                    if t >= startTimeDT:
                        cutIndex = plotTi.index(t)
                        break
                plotTi = plotTi[cutIndex:]
                plotTemps = plotTemps[cutIndex:]

            animated_plot.set_xdata(plotTi)
            animated_plot.set_ydata(plotTemps)

            # Only update the x-axis limits for sliding windows since doing so partially breaks pan-zoom functionality
            if dataSeconds > 0:
                plt.xlim(left = plotTi[0] - timedelta(seconds=100), right = plotTi[-1] + timedelta(seconds=100))

            plt.draw()
            plt.pause(5)
        

        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor BSB headset temperature from log file.")
    parser.add_argument("--logfile", type=str, default=LOGFILE, help="Path to the log file.")
    parser.add_argument("--lastHours", "-H", type=int, help="Show this many previous hours of data. Will be added to other --lastX arguments")
    parser.add_argument("--lastMinutes", "-M", type=int, help="Show this many previous minutes of data. Will be added to other --lastX arguments")
    parser.add_argument("--lastSeconds", "-S", type=int, help="Show this many previous seconds of data. Will be added to other --lastX arguments")
    parser.add_argument("--startTime", "-s", help="Show data starting from this time. Not compatible with --lastX arguments. Format: 'YYYY-MM-DD HH:MM:SS'")
    parser.add_argument("--endTime", "-e", help="Show data ending at this time. Not compatible with --lastX arguments. Format: 'YYYY-MM-DD HH:MM:SS'")
    args = parser.parse_args()

    LOGFILE = args.logfile

    main(args)