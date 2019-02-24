from .Worker import WorkerManager, WORKERS
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

	# Speculative loading
	if "page" in url:
		cur_page = "".join([c for c in url.split("page")[1] if c.isdigit()])

		if last_speculative != url.replace("page", ""):
			last_speculative = url.replace("page", "")
			last_speculative_page = int(cur_page)

		awaites = []
		for i in range(WORKERS):
			next_page = last_speculative_page + i + 1
			next_url = url.replace(
				"page{}".format(cur_page),
				"page{}".format(next_page)
			)
			awaites.append(worker_manager.enqueue(next_url))

		await asyncio.gather(*awaites)

		last_speculative_page = next_page

	soup = await worker_manager.query(url)
	return soup