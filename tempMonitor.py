#!/usr/bin/env python3

import re
import time
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, date
import argparse
import sys

# Raw string avoids needing to escape backslashes
LOGFILE = r"C:\Program Files (x86)\Steam\steamapps\common\Bigscreen Beyond Driver\bin\log.txt"

EXIT=False

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

# Parse datetime string which may be either full date+time or just time
# If just time, assume today's date
def parseDT(dtString):
    try:
        return datetime.strptime(dtString, r"%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass

    time = datetime.strptime(dtString, r"%H:%M:%S")
    today = date.today()

    final_datetime = datetime(
        year = today.year, 
        month = today.month, 
        day = today.day, 
        hour = time.hour, 
        minute = time.minute
    )

    return final_datetime

def on_close(event):
    global EXIT
    EXIT = True
    print("Window Closed. Exiting...")
    sys.exit(0)

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
        print(f"Showing data from {parseDT(args.startTime)} to {parseDT(args.endTime)}.")
    elif args.startTime:
        print(f"Showing data from {parseDT(args.startTime)} to present.")
    elif args.endTime:
        print(f"Showing data from start to {parseDT(args.endTime)}.")
    else:
        print("Showing all data.")
    

    print("Opening and parsing log file")
    with open(LOGFILE, "r") as lf:
        ti = []
        temps = []

        # First load all the existing data points
        for line in lf:
            # Only parse lines starting with YYYY-MM-DD string
            if re.match(r'^\d{4}-\d{2}-\d{2}', line):
                time = line.split(",")[0]
                timeDT = parseDT(time)
                ti.append(timeDT)

                temp = line.split(",")[2]
                temps.append(float(temp))

        #plt.plot(ti, temps)
        #plt.scatter(ti, temps)
        plt.xlabel("Time")
        plt.ylabel("Temperature (C)")
        plt.title("BSB Temperature over Time")
        animated_plot = plt.plot(ti, temps, 'bo')[0]

        print("File parsed, preparing plot for display...")
        fig = plt.figure(1)
        fig.canvas.mpl_connect('close_event', on_close)

        if args.endTime:
            endTimeDT = parseDT(args.endTime)
            plt.xlim(right = endTimeDT + timedelta(seconds=100))
            if args.startTime:
                startTimeDT = parseDT(args.startTime)
                plt.xlim(left = startTimeDT - timedelta(seconds=100))
            plt.show()
            return
        

        # turn interactive mode on to enable real-time updating
        plt.ion() 

        if args.startTime:
            ll = parseDT(args.startTime) - timedelta(seconds=100)
            plt.xlim(left = ll)
        #    print(f"Left limit: {ll}")
        #plt.draw()

        # Plot new data points as they are written to the log file
        for line in follow(lf):
            if re.match(r'^\d{4}-\d{2}-\d{2}', line):
                time = line.split(",")[0]
                thisTime = parseDT(time)
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
                startTimeDT = parseDT(args.startTime)
                cutIndex = None
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
    parser.add_argument("--startTime", "-s", help="Show data starting from this time. Not compatible with --lastX arguments. Format: 'YYYY-MM-DD HH:MM:SS'  or 'HH:MM:SS' (assume today's date).")
    parser.add_argument("--endTime", "-e", help="Show data ending at this time. Not compatible with --lastX arguments. Format: 'YYYY-MM-DD HH:MM:SS' or 'HH:MM:SS' (assume today's date).")
    args = parser.parse_args()

    LOGFILE = args.logfile

    main(args)