import datetime
from ..WebAPI import HABR, parsePage

def textToInteger(text):
	if "k" in text:
		coeff = 1000
	else:
		coeff = 1

	text = "".join(c for c in text if c.isdigit() or c == ",").replace(",", ".")
	if text == "":
		return 0

	return int(float(text) * coeff)


def parseDate(date):
	if "сегодня в " in date:
		time_obj = datetime.datetime.strptime(date, "сегодня в %H:%M").time()
		date_obj = datetime.date.today()
	elif "вчера в " in date:
		time_obj = datetime.datetime.strptime(date, "вчера в %H:%M").time()
		date_obj = datetime.date.today() - datetime.timedelta(days=1)
	else:
		day, month, year, _, time = date.split()
		month = {
			"января": 1,
			"февраля": 2,
			"марта": 3,
			"апреля": 4,
			"мая": 5,
			"июня": 6,
			"июля": 7,
			"августа": 8,
			"сентября": 9,
			"октября": 10,
			"ноября": 11,
			"декабря": 12
		}[month]
		date_obj = datetime.date(year=int(year), month=month, day=int(day))
		time_obj = datetime.datetime.strptime(time, "%H:%M").time()

	datetime_obj = datetime.datetime.combine(date_obj, time_obj)
	return datetime_obj


# Returns a list of all hubs (their names, URLs and so on)
def gatherHubList():
	hubs = []

	url = "/ru/hubs/"

	while True:
		page = parsePage(url)

		# Parse page
		for hub in page.find_all(class_="content-list__item_hubs"):
			link = hub.find(class_="list-snippet__title-link")
			href = link["href"]
			hub_id = href.replace(HABR + "/ru/hub/", "").replace("/", "")

			subscribers = textToInteger(
				hub.find(class_="stats__counter_subscribers").text
			)
			rating = textToInteger(
				hub.find(class_="stats__counter_rating").text
			)

			hubs.append({
				"href": href,
				"id": hub_id,
				"name": link.text,
				"subscribers": subscribers,
				"rating": rating
			})

		# Next page
		next_link = page.find(id="next_page")
		if next_link is None:
			break
		url = next_link["href"]

	return hubs


def gatherPosts(url):
	posts = []

	page = parsePage(url)
	gather_date = datetime.datetime.now()
	for post in page.find_all(class_="post"):
		# Article
		is_article = bool(post.find(class_="preview-data__title-link"))

		if not is_article:
			# Normal post
			# Title
			address = (
				post.find(class_="post__title_link")["href"]
					.replace(HABR + "/ru/", "")
					.rstrip("/")
			)
			title = post.find(class_="post__title").text.strip()
			# Author
			author_href = post.find(class_="user-info")["href"]
			author = (
				author_href.replace(HABR + "/ru/users/", "").replace("/", "")
			)
			# Date/time
			date = parseDate(post.find(class_="post__time").text)
			# Hubs
			hubs = [
				hub["href"].replace(HABR + "/ru/hub/", "").replace("/", "")
				for hub in post.find_all(class_="hub-link")
				if not hub["href"].startswith(HABR + "/ru/company/")
			]
			is_blog = any(
				hub["href"].startswith(HABR + "/ru/company/")
				for hub in post.find_all(class_="hub-link")
			)
			# Labels
			labels = [
				label.text for label in post.find_all(class_="post__type-label")
			]
			is_translation = "Перевод" in labels
			is_tutorial = "Tutorial" in labels
		else:
			# Article
			address = (
				post.find(class_="preview-data__title-link")["href"]
					.replace(HABR + "/ru/", "")
					.rstrip("/")
			)
			title = post.find(class_="preview-data__title-link").text.strip()
			# Author
			author_href = ""
			author = ""
			# Date/time
			date = parseDate(
				post.find(class_="preview-data__time-published").text
			)
			# Hubs
			hubs = [
				hub["href"].replace(HABR + "/ru/hub/", "").replace("/", "")
				for hub in (
					post.find(class_="preview-data__hubs")
						.find_all(class_="list__item-link")
				)
			]
			is_blog = True
			# Labels
			is_translation = False
			is_tutorial = False

		# Rating
		rating_title = post.find(class_="voting-wjt__counter")["title"]
		upvotes = float(rating_title.split("↑")[1].split(" ")[0])
		downvotes = float(rating_title.split("↓")[1])
		# Bookmarks
		bookmarks = textToInteger(
			post.find(class_="bookmark__counter").text
		)
		# Views
		views = textToInteger(
			post.find(class_="post-stats__views-count").text
		)
		# Comments
		comments_node = post.find(class_="post-stats__comments-count")
		if comments_node is None:
			comments = 0
		else:
			comments = textToInteger(comments_node.text)

		posts.append({
			"is_article": is_article,
			"address": address,
			"title": title,
			"author": author,
			"date": date.timestamp(),
			"hubs": hubs,
			"is_blog": is_blog,
			"is_translation": is_translation,
			"is_tutorial": is_tutorial,
			"upvotes": upvotes,
			"downvotes": downvotes,
			"bookmarks": bookmarks,
			"views": views,
			"comments": comments
		})

	next_link = page.find(id="next_page")
	if next_link is None:
		next_url = None
	else:
		next_url = next_link["href"]
	return posts, next_url