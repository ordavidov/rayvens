import os
import ray
from ray import serve
import requests

from rayvens import kamel


@ray.remote(num_cpus=0, resources={'camel': 1})
class Camel:
    def __init__(self):
        self.client = serve.start(http_options={'host': '0.0.0.0'})

    def addSink(self, name, topic, to):
        integration = kamel.Integration(name, [{
            'from': {
                'uri': f'platform-http:/{name}',
                'steps': [{
                    'to': to
                }]
            }
        }])
        topic.subscribe.remote(
            lambda data: requests.post(f'{integration.url}/{name}', data),
            name)
        topic._register.remote(name, integration)

    def addSource(self, name, topic, url, period=3000, prefix='/ravyens'):
        async def publish(data):
            topic.publish.remote(await data.body())

        self.client.create_backend(name,
                                   publish,
                                   config={'num_replicas': 1},
                                   ray_actor_options={'num_cpus': 0})
        self.client.create_endpoint(name,
                                    backend=name,
                                    route=f'{prefix}/{name}',
                                    methods=['POST'])
        endpoint = 'http://localhost:8000'
        namespace = os.getenv('KUBE_POD_NAMESPACE')
        if namespace is not None:
            with open('/etc/podinfo/labels', 'r') as f:
                for line in f:
                    k, v = line.partition('=')[::2]
                    if k == 'component':
                        endpoint = f'http://{v[1:-2]}.{namespace}.svc.cluster.local:8000'
                        break
        integration = kamel.Integration(name, [{
            'from': {
                'uri': f'timer:tick?period={period}',
                'steps': [{
                    'to': url
                }, {
                    'to': f'{endpoint}{prefix}/{name}'
                }]
            }
        }])
        topic._register.remote(name, integration)

    def disconnectAll(self, topic):
        integrations = ray.get(topic._disconnect.remote())
        for i in integrations:
            i['integration'].cancel()


@ray.remote(num_cpus=0)
class Topic:
    def __init__(self, name):
        self.name = name
        self.subscribers = []
        self.integrations = []

    def subscribe(self, f, name=None):
        self.subscribers.append({'f': f, 'name': name})

    def publish(self, *args, **kwargs):
        for s in self.subscribers:
            s['f'](*args, **kwargs)

    def _register(self, name, integration):
        self.integrations.append({'name': name, 'integration': integration})

    def _disconnect(self):
        self.subscribers = []
        integrations = self.integrations
        self.integrations = []
        return integrations
