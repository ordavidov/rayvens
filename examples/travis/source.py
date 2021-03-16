import asyncio
import json
import ray
import rayvens

ray.init(address='auto')

client = rayvens.Client()

source_config = dict(
    kind='http-source',
    url='http://financialmodelingprep.com/api/v3/quote-short/AAPL?apikey=demo',
    period=3000)
source = client.create_stream('http', source=source_config)


@ray.remote
class Counter:
    def __init__(self):
        self.count = 0
        self.ready = asyncio.Event()

    def append(self, event):
        print('AAPL is', json.loads(event)[0]['price'])
        self.count += 1
        if self.count > 5:
            self.ready.set()

    async def wait(self):
        await self.ready.wait()


counter = Counter.remote()

source >> counter

ray.get(counter.wait.remote(), timeout=180)
