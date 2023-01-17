import datetime
import time as timeModule
import praw
import xlsxwriter

reddit = praw.Reddit(
    client_id="#",
    client_secret="#",
    password="#",
    user_agent="#",
    username="#",
)

post_id = input("Post ID: ")
date_keep = input("Date of interest in YY/MM/DD format: ")
time_interval = str(input("Seconds between datapoints: "))

print("Starting...")
t0 = timeModule.perf_counter()

submission = reddit.submission(id=post_id)
comment_times = []
submission.comments.replace_more(limit=None)
for comment in submission.comments.list():
    comment = comment.created_utc
    comment = datetime.datetime.fromtimestamp(comment)
    comment = comment.strftime("%y/%m/%d - %H:%M:%S")
    comment_times.append(comment)

comment_times = sorted(comment_times)
comment_times_limited = [i for i in comment_times if date_keep in str(i)]
comment_times_only = [i.replace(i[:11], "") for i in comment_times_limited]

print(
    "There was "
    + str(len(comment_times_only))
    + " comments posted during the selected day."
)
t1 = timeModule.perf_counter()
print("It took " + str(round((t1 - t0), 1)) + " seconds to collect them.")

list_secs = [
    sum(int(x) * 60**i for i, x in enumerate(reversed(g.split(":"))))
    for g in comment_times_only
]
time_interval_z = "00"
first_e = comment_times_only[0]
point_zero = first_e.replace(first_e[-2:], time_interval_z)
secs_z = sum(int(x) * 60**i for i, x in enumerate(reversed(point_zero.split(":"))))
list_final = []

while True:
    if secs_z > list_secs[-1]:
        break
    secs_o = str(int(secs_z) + int(time_interval))
    list_OI = [i for i in list_secs if i > int(secs_z) and i < int(secs_o)]
    secs_ZR = str(datetime.timedelta(seconds=secs_z))
    list_final.append([secs_ZR, len(list_OI)])
    secs_z += int(time_interval)

workbook = xlsxwriter.Workbook("dataPast.xlsx")
worksheet = workbook.add_worksheet()
worksheet.write(0, 0, "Time")
worksheet.write(0, 1, "New Comments")
row = 1
for time, delta in list_final:
    worksheet.write(row, 0, time)
    worksheet.write(row, 1, delta)
    row += 1
workbook.close()

print("Done.")
t2 = timeModule.perf_counter()
print("The script took " + str(round((t2 - t0), 1)) + " seconds to run.")
