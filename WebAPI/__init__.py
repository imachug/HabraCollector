from .Worker import WorkerManager, WORKERS

HABR = "https://habr.com"

worker_manager = WorkerManager()


def getTotalTraffic():
	return worker_manager.total_traffic

async def initWorkers():
	await worker_manager.initWorkers()
async def workerLoop():
	await worker_manager.startWorkers()

async def parsePage(url):
	if HABR not in url:
		# Relative URL
		url = HABR + url

	# Speculative loading
	if "page" in url:
		cur_page = "".join([c for c in url.split("page")[1] if c.isdigit()])
		for i in range(1, WORKERS):
			next_page = int(cur_page) + i
			next_url = url.replace(
				"page{}".format(cur_page),
				"page{}".format(next_page)
			)
			await worker_manager.enqueue(next_url)

	soup = await worker_manager.query(url)
	return soup