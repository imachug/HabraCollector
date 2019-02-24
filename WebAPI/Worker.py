import aiohttp
import asyncio
from bs4 import BeautifulSoup

WORKERS = 15

async def _parseAndLoad(session, url):
	for _ in range(20):
		try:
			async with session.get(url) as res:
				html = await res.text()
				soup = BeautifulSoup(html, "html5lib")
				return soup, len(html)
		except Exception:
			pass
	raise ValueError("Too many retries")


class Worker:
	def __init__(self, session, queue, id):
		self._session = session
		self._queue = queue
		self._id = id

	async def loop(self):
		while True:
			url, callback = await self._queue.get()
			callback(*(await _parseAndLoad(self._session, url)))
			self._queue.task_done()

class WorkerManager:
	def __init__(self):
		self._queue = None
		self._cache = {}
		self._cached = {}
		self.total_traffic = 0

	async def initWorkers(self):
		self._session = aiohttp.ClientSession()
		self._queue = asyncio.Queue()

	async def startWorkers(self):
		loops = []
		for i in range(WORKERS):
			loops.append(Worker(self._session, self._queue, i).loop())
		await asyncio.gather(*loops)

	def enqueue(self, url):
		if url not in self._cache:
			self._cache[url] = False  # in progress
			self._cached[url] = asyncio.Event()
			self._queue.put_nowait((url, lambda *args: self._save(url, *args)))

	def clearQueue(self):
		try:
			while True:
				self._queue.get_nowait()
				self._queue.task_done()
		except Exception:
			return

	def _save(self, url, soup, traffic):
		self.total_traffic += traffic
		self._cache[url] = soup
		self._cached[url].set()

	async def query(self, url):
		if url not in self._cache:
			# Haven't even started, enqueue
			self.enqueue(url)
		if not self._cache[url]:
			# In progress
			await self._cached[url].wait()  # wait for result
		# Return
		soup = self._cache[url]
		del self._cache[url]
		del self._cached[url]
		return soup