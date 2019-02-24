import aiohttp
import asyncio
from bs4 import BeautifulSoup

WORKERS = 15
SPECULATIVE = 1

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
			while self._queue == []:
				await asyncio.sleep(0.001)

			url, callback = self._queue.pop(0)
			callback(*(await _parseAndLoad(self._session, url)))

class WorkerManager:
	def __init__(self):
		self._queue = []
		self._cache = {}
		self._cached = {}
		self.total_traffic = 0

	async def startWorkers(self):
		loops = []
		for i in range(WORKERS):
			session = aiohttp.ClientSession()
			loops.append(Worker(session, self._queue, i).loop())
		await asyncio.gather(*loops)

	def enqueue(self, url, force=False):
		if url not in self._cache:
			self._cache[url] = False  # in progress
			self._cached[url] = asyncio.Event()
			value = (url, lambda *args: self._save(url, *args))
			if force:
				self._queue.insert(0, value)
			else:
				self._queue.append(value)

	def clearQueue(self):
		self._queue.clear()

	def _save(self, url, soup, traffic):
		self.total_traffic += traffic
		self._cache[url] = soup
		self._cached[url].set()

	async def query(self, url):
		if url not in self._cache:
			# Haven't even started, enqueue
			self.enqueue(url, force=True)
		if not self._cache[url]:
			# In progress
			await self._cached[url].wait()  # wait for result
		# Return
		soup = self._cache[url]
		del self._cache[url]
		del self._cached[url]
		return soup