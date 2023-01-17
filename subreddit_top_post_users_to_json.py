import json
import praw
import datetime

reddit = praw.Reddit(
    client_id="#",
    client_secret="#",
    password="#",
    user_agent="#",
    username="#",
)


class User:
    def __init__(self, name):
        self.name = name
        self.posts = []
        self.comments = []

    def add_post(self, post_id, post_date, post_time, post_score, post_flair):
        self.post = {
            "post_id": post_id,
            "post_date": post_date,
            "post_time": post_time,
            "post_score": post_score,
            "post_flair": post_flair,
        }
        self.posts.append(self.post)

    def add_comment(
        self, comment_id, comment_date, comment_time, comment_score, comment_flair
    ):
        self.comment = {
            "comment_id": comment_id,
            "comment_date": comment_date,
            "comment_time": comment_time,
            "comment_score": comment_score,
            "comment_flair": comment_flair,
        }
        self.comments.append(self.comment)

    def to_dict(self):
        return {"name": self.name, "posts": self.posts, "comments": self.comments}


users = []
posts_ok = 0
subreddit_name = "python"

subreddit = reddit.subreddit(subreddit_name)
submissions = subreddit.top(limit=None)
print(f"\nChecking top posts from r/{subreddit}\n")
for submission in submissions:
    post = reddit.submission(id=submission)
    post_id = submission.id
    post_date = post.created_utc
    post_date_clean = datetime.datetime.fromtimestamp(post_date)
    post_date_cleaner = post_date_clean.strftime("%d.%m.%y")
    post_time = post_date_clean.strftime("%H:%M:%S")
    post_date_year = int(post_date_clean.strftime("%y"))

    if post_date_year == 22:
        posts_ok += 1
        if post.author:
            post_author = post.author.name
        else:
            post_author = None
        post_score = post.score
        post_flair = post.link_flair_text

        if not any(user.name == post_author for user in users):
            users.append(User(post_author))
        user_object = [user for user in users if user.name == post_author][0]
        user_object.add_post(
            post_id, post_date_cleaner, post_time, post_score, post_flair
        )

        post.comments.replace_more(limit=None)
        comments_list = post.comments.list()
        print(
            f"Checking post: {post.title[:50] + '...' if len(post.title)>50 else post.title} ({len(comments_list)} comments)"
        )

        for comment in comments_list:
            if comment.author:
                comment_id = comment.id
                comment_author = comment.author.name
                comment_score = comment.score
                comment_flair = comment.author_flair_text
                comment_date = comment.created_utc
                comment_date_clean = datetime.datetime.fromtimestamp(comment_date)
                comment_date_cleaner = comment_date_clean.strftime("%d.%m.%y")
                comment_time = comment_date_clean.strftime("%H:%M:%S")

                if not any(user.name == comment_author for user in users):
                    users.append(User(comment_author))
                user_object = [user for user in users if user.name == comment_author][0]
                user_object.add_comment(
                    comment_id,
                    comment_date_cleaner,
                    comment_time,
                    comment_score,
                    comment_flair,
                )

print(f"\nDone\nValid posts: {posts_ok}")

users_dict = [user.to_dict() for user in users]
with open("users.json", "w") as f:
    json.dump(users_dict, f)
