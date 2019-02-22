import urllib.request
from bs4 import BeautifulSoup

HABR = "https://habr.com"

total_traffic = {"traffic": 0}

def parsePage(url):
	if HABR not in url:
		# Relative URL
		url = HABR + url
	html = urllib.request.urlopen(url).read()
	total_traffic["traffic"] += len(html)
	soup = BeautifulSoup(html, "html5lib")
	return soup