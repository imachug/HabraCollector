import aiohttp
import asyncio
from bs4 import BeautifulSoup

WORKERS = 8

async def _parseAndLoad(session, url):
	async with session.get(url) as res:
		html = await res.text()
		soup = BeautifulSoup(html, "html5lib")
		return soup, len(html)


class Worker:
	def __init__(self, session, queue):
		self._session = session
		self._queue = queue

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
		for _ in range(WORKERS):
			loops.append(Worker(self._session, self._queue).loop())
		await asyncio.gather(*loops)

	async def enqueue(self, url):
		if url not in self._cache:
			self._cache[url] = False  # in progress
			self._cached[url] = asyncio.Event()
			await self._queue.put((url, lambda *args: self._save(url, *args)))

	def _save(self, url, soup, traffic):
		self.total_traffic += traffic
		self._cache[url] = soup
		self._cached[url].set()

	async def query(self, url):
		if url not in self._cache:
			# Haven't even started, enqueue
			await self.enqueue(url)
		if not self._cache[url]:
			# In progress
			await self._cached[url].wait()  # wait for result
		# Return
		soup = self._cache[url]
		del self._cache[url]
		del self._cached[url]
		return soup