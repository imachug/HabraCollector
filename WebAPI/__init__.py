from .Worker import WorkerManager, WORKERS, SPECULATIVE
import asyncio

HABR = "https://habr.com"

worker_manager = WorkerManager()

def getTotalTraffic():
	return worker_manager.total_traffic

async def initWorkers():
	await worker_manager.initWorkers()
async def workerLoop():
	await worker_manager.startWorkers()

last_speculative = ""
last_speculative_page = 0

async def parsePage(url):
	global last_speculative, last_speculative_page

	if HABR not in url:
		# Relative URL
		url = HABR + url


	cur_future = worker_manager.query(url)

	# Speculative loading
	if "page" in url:
		cur_page = "".join([c for c in url.split("page")[1] if c.isdigit()])
	else:
		cur_page = 1
	if last_speculative != url.split("page")[0]:
		last_speculative = url.split("page")[0]
		last_speculative_page = int(cur_page)
		worker_manager.clearQueue()

	next_page = 0
	for i in range(SPECULATIVE):
		next_page = last_speculative_page + i + 1
		next_url = url.replace(
			"page{}".format(cur_page),
			"page{}".format(next_page)
		)
		worker_manager.enqueue(next_url)

	last_speculative_page = next_page


	soup = await cur_future
	return soup