#!/usr/bin/env python3

import re
import time
import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, date
import argparse
import sys
import queue
import threading

# Raw string avoids needing to escape backslashes
LOGFILE = r"C:\Program Files (x86)\Steam\steamapps\common\Bigscreen Beyond Driver\bin\log.txt"

NEWLINES = queue.Queue()

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

        NEWLINES.put(line)
        #yield line

# Parse datetime string which may be either full date+time or just time
# If just time, assume today's date
def parseDT(dtString):
    dtFormmat = "%Y-%m-%d %H:%M:%S"
    tFormat = "%H:%M:%S"

    try:
        return datetime.strptime(dtString, dtFormmat)
    except ValueError:
        pass

    time = datetime.strptime(dtString, tFormat)
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
    print("Window Closed. Exiting...")
    sys.exit(0)

def main(args):
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
        mbt = []
        dlt = []
        drt = []

        # First load all the existing data points
        for line in lf:
            # Only parse lines starting with YYYY-MM-DD string
            if re.match(r'^\d{4}-\d{2}-\d{2}', line):
                time = line.split(",")[0]
                timeDT = parseDT(time)
                ti.append(timeDT)

                mbTemp = line.split(",")[2]
                mbt.append(float(mbTemp))

                dlTemp = float(line.split(",")[3])
                drTemp = float(line.split(",")[4])

                if dlTemp < 0:
                    dlt.append(0)
                else:
                    dlt.append(dlTemp)

                if drTemp < 0:
                    drt.append(0)
                else:
                    drt.append(drTemp)

        #plt.plot(ti, mbt)
        #plt.scatter(ti, mbt)
        plt.xlabel("Time")
        plt.ylabel("Temperature (C)")
        plt.title("BSB Temperature over Time")
        #animated_plot = plt.plot(ti, mbt, 'bo')[0]

        animated_plot = plt.plot(ti, mbt, 'o', label="MainboardTemp")[0]
        plot2 = plt.plot(ti, dlt, 's', label="DisplayLeftTemp")[0]
        plot3 = plt.plot(ti, drt, 'v', label="DisplayRightTemp")[0]

        #animated_plot = plt.scatter(ti, mbt, label="MainboardTemp")
        #plot2 = plt.scatter(ti, dlt, label="DisplayLeftTemp")
        #plot3 = plt.scatter(ti, drt, label="DisplayRightTemp")
        
        plt.legend(loc='best')

        fig = plt.figure(1)
        fig.canvas.mpl_connect('close_event', on_close)

        print("File parsed, preparing plot for display...")

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

        plt.draw()

        # Start thread that watches file and adds new lines to queue
        watcher = threading.Thread(target=follow, args=(lf,))
        watcher.start()

        # Plot new data points as they are copied from the log file to the queue
        while True:
            try:
                line = NEWLINES.get(block=False)
            except queue.Empty:
                #print("No new lines yet...")
                plt.draw()
                plt.pause(1)
                continue

            # Only parse lines starting with YYYY-MM-DD string
            if re.match(r'^\d{4}-\d{2}-\d{2}', line):
                time = line.split(",")[0]
                thisTime = parseDT(time)
                ti.append(thisTime)

                temp = line.split(",")[2]
                mbt.append(float(temp))

                dlTemp = float(line.split(",")[3])
                drTemp = float(line.split(",")[4])

                if dlTemp < 0:
                    dlt.append(0)
                else:
                    dlt.append(dlTemp)

                if drTemp < 0:
                    drt.append(0)
                else:
                    drt.append(drTemp)
            
            recentTimestamp = ti[-1]
            plotTi = ti
            plotMbt = mbt
            plotDlt = dlt
            plotDrt = drt

            if dataSeconds > 0:
                for t in ti:
                    if (recentTimestamp - t).total_seconds() <= dataSeconds:
                        cutIndex = ti.index(t)
                        break
                plotTi = ti[cutIndex:]
                plotMbt = mbt[cutIndex:]
                plotDlt = dlt[cutIndex:]
                plotDrt = drt[cutIndex:]

            
            elif args.startTime:
                startTimeDT = parseDT(args.startTime)
                cutIndex = None
                for t in plotTi:
                    if t >= startTimeDT:
                        cutIndex = plotTi.index(t)
                        break
                plotTi = plotTi[cutIndex:]
                plotMbt = plotMbt[cutIndex:]
                plotDlt = plotDlt[cutIndex:]
                plotDrt = plotDrt[cutIndex:]

            animated_plot.set_xdata(plotTi)
            animated_plot.set_ydata(plotMbt)
            plot2.set_xdata(plotTi)
            plot2.set_ydata(plotDlt)
            plot3.set_xdata(plotTi)
            plot3.set_ydata(plotDrt)

            # Only update the x-axis limits for sliding windows since doing so partially breaks pan-zoom functionality
            if dataSeconds > 0:
                plt.xlim(left = plotTi[0] - timedelta(seconds=100), right = plotTi[-1] + timedelta(seconds=100))

            plt.draw()
            plt.pause(5)
        

        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor BSB headset temperature from log file.")
    parser.add_argument("--logfile", "-f", type=str, default=LOGFILE, help=f"Path to the log file. Default is '{LOGFILE}'")
    parser.add_argument("--lastHours", "-H", type=int, help="Show this many previous hours of data. Will be added to other --lastX arguments")
    parser.add_argument("--lastMinutes", "-M", type=int, help="Show this many previous minutes of data. Will be added to other --lastX arguments")
    parser.add_argument("--lastSeconds", "-S", type=int, help="Show this many previous seconds of data. Will be added to other --lastX arguments")
    parser.add_argument("--startTime", "-s", help="Show data starting from this time. Not compatible with --lastX arguments. Format: 'YYYY-MM-DD HH:MM:SS'  or 'HH:MM:SS' (assume today's date).")
    parser.add_argument("--endTime", "-e", help="Show data ending at this time. Not compatible with --lastX arguments. Format: 'YYYY-MM-DD HH:MM:SS' or 'HH:MM:SS' (assume today's date).")
    args = parser.parse_args()

    LOGFILE = args.logfile

    main(args)