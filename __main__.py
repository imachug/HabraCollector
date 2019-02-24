import os, json, chalk
from .WebAPI import total_traffic
from .LinkGatherer import gatherHubList, gatherPosts

SAVE_LIMIT = 500

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.makedirs("cache", exist_ok="True")

if os.path.exists("cache/hubs.json"):
	print(chalk.green("Getting hub list from cache"))
	with open("cache/hubs.json") as f:
		hubs = json.loads(f.read())
else:
	print(chalk.green("Gathering hubs list..."))
	hubs = gatherHubList()
	print(chalk.green("Saving to cache"))
	with open("cache/hubs.json", "w") as f:
		f.write(json.dumps(hubs))

print()
print()
print("Found", len(hubs), "hubs:")
for hub in hubs:
	print("#{}{}{}{}".format(
		chalk.yellow(hub["id"].ljust(30)),
		chalk.green(str(hub["subscribers"]).ljust(10)),
		chalk.magenta(str(hub["rating"]).ljust(10)),
		hub["name"]
	))
print()
print()

if os.path.exists("cache/gathered_posts.json"):
	print(chalk.green("Getting gathered posts list from cache"))
	with open("cache/gathered_posts.json") as f:
		gathered_posts = set(json.loads(f.read()))
else:
	gathered_posts = set()

if os.path.exists("cache/gathered_hubs.json"):
	print(chalk.green("Getting gathered hubs list from cache"))
	with open("cache/gathered_hubs.json") as f:
		gathered_hubs = json.loads(f.read())
else:
	gathered_hubs = {}

posts = []
expected_traffic = 1024 * 1024 * 512
for i, hub in enumerate(hubs):
	print(
		chalk.green("Handling hub"),
		"#{}".format(chalk.yellow(hub["id"])),
		"{}/{}".format(chalk.cyan(str(i)), chalk.blue(str(len(hubs))))
	)

	if hub["id"] not in gathered_hubs:
		gathered_hubs[hub["id"]] = {
			"full": False,
			"url": hub["href"]
		}
	elif gathered_hubs[hub["id"]]["full"]:
		continue

	url = gathered_hubs[hub["id"]]["url"]
	while url is not None:
		print("URL:", chalk.blue(url).ljust(60), end="")
		page_posts, url = gatherPosts(url)
		cnt = 0
		for post in page_posts:
			if post["address"] not in gathered_posts:
				gathered_posts.add(post["address"])
				posts.append(post)
				cnt += 1
		print(
			chalk.green("+{} posts".format(cnt).ljust(10)),
			chalk.yellow("{} total".format(len(posts)).ljust(10)),
			chalk.magenta(
				"{} MiB traffic".format(
					total_traffic["traffic"] // (1024 * 1024)
				)
			)
		)

		gathered_hubs[hub["id"]]["url"] = url

		if len(posts) >= SAVE_LIMIT:
			print(chalk.green("Saving to disk"))
			with open("cache/gathered_posts.json", "w") as f:
				f.write(json.dumps(list(gathered_posts)))
			with open("cache/gathered_hubs.json", "w") as f:
				f.write(json.dumps(gathered_hubs))
			file_name = "cache/posts{}.json".format(len(gathered_posts))
			with open(file_name, "w") as f:
				f.write(json.dumps(posts))
			posts = []

		if total_traffic["traffic"] >= expected_traffic:
			print(
				chalk.red(
					"Reached {} GiB".format(
						expected_traffic / (1024 * 1024 * 1024)
					)
				)
			)
			expected_traffic += 1024 * 1024 * 512

	gathered_hubs[hub["id"]]["full"] = True

if posts != []:
	print(chalk.green("Saving to disk"))
	with open("cache/gathered_posts.json", "w") as f:
		f.write(json.dumps(list(gathered_posts)))
	with open("cache/gathered_hubs.json", "w") as f:
		f.write(json.dumps(gathered_hubs))
	file_name = "cache/posts{}.json".format(len(gathered_posts))
	with open(file_name, "w") as f:
		f.write(json.dumps(posts))
	posts = []


print()
print()

all_posts = []
if os.path.exists("cache/all.txt"):
	print(chalk.green("Getting all posts from cache"))
	with open("cache/all.txt", encoding="utf-8") as f:
		for post in f:
			all_posts.append(json.loads(post))
else:
	print(chalk.green("Joining posts"))
	all_posts = []
	for file in os.listdir("cache"):
		if file.startswith("posts"):
			print("File:", chalk.blue(file))
			with open("cache/{}".format(file)) as f:
				all_posts += json.loads(f.read())
	print(chalk.green("Saving"))
	with open("cache/all.txt", "w", encoding="utf-8") as f:
		for post in all_posts:
			f.write(json.dumps(post, ensure_ascii=False) + "\n")

print()
print()
print(chalk.green("Finished."))
print("Total posts:  ", len(all_posts))
print("Total authors:", len(set(post["author"] for post in all_posts)))