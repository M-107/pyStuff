import json
from datetime import datetime

file = open(r"C:\Users\marti\users.json", "r", encoding="UTF-8").read()
users = json.loads(file)

user_flairs = []
for user in users:
    if user["comments"]:
        last_comment = []
        for comment in user["comments"]:
            if last_comment:
                last_date = datetime.strptime(last_comment[0], "%d.%m.%y")
                current_date = datetime.strptime(comment["comment_date"], "%d.%m.%y")
                if current_date > last_date:
                    last_comment = [comment["comment_date"], comment["comment_flair"]]
            else:
                last_comment = [comment["comment_date"], comment["comment_flair"]]
        user_flairs.append(last_comment[1])

post_flairs = []
for user in users:
    if user["posts"]:
        for post in user["posts"]:
            post_flairs.append(post["post_flair"])

checked_comment_flairs = []
for flair in user_flairs:
    if flair not in checked_comment_flairs:
        print(f"{flair} - {user_flairs.count(flair)}")
        checked_comment_flairs.append(flair)

checked_post_flairs = []
for flair in post_flairs:
    if flair not in checked_post_flairs:
        print(f"{flair} - {post_flairs.count(flair)}")
        checked_post_flairs.append(flair)
