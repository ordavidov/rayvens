import atexit
import ray
from ray import serve
from rayvens.core.camel_anywhere.kamel_backend import KamelBackend
from rayvens.core.camel_anywhere.mode import mode, RayKamelExecLocation
from rayvens.core.camel_anywhere import kamel
from rayvens.core.utils import utils


def start(prefix, camel_mode):
    camel = None
    if camel_mode == 'local':
        mode.location = RayKamelExecLocation.LOCAL
        camel = CamelAnyNode.remote(prefix, camel_mode, mode)
    elif camel_mode == 'mixed':
        mode.location = RayKamelExecLocation.MIXED
        camel = CamelAnyNode.remote(prefix, camel_mode, mode)
    elif camel_mode == 'operator':
        mode.location = RayKamelExecLocation.CLUSTER
        camel = CamelAnyNode.options(resources={
            'head': 1
        }).remote(prefix, camel_mode, mode)
    else:
        raise RuntimeError("Unsupported camel mode.")

    # Setup what happens at exit.
    atexit.register(camel.exit.remote)
    return camel


@ray.remote(num_cpus=0)
class CamelAnyNode:
    def __init__(self, prefix, camel_mode, mode):
        if camel_mode in ["local", "mixed"]:
            self.client = serve.start()
        else:
            self.client = serve.start(http_options={
                'host': '0.0.0.0',
                'location': 'EveryNode'
            })
        self.prefix = prefix
        self.camel_mode = mode
        self.mode = mode
        self.kamel_backend = None
        self.endpoint_id = -1
        self.integration_id = -1
        self.invocations = []

    def add_source(self, name, topic, source):
        if source['kind'] is None:
            raise TypeError('A Camel source needs a kind.')
        if source['kind'] not in ['http-source']:
            raise TypeError('Unsupported Camel source.')
        source_url = source['url']
        period = source.get('period', 1000)
        # TODO: do it like this.
        # route = f'{self.prefix}' + source['route']
        route = f'{self.prefix}/{name}'

        # Set endpoint and integration names.
        endpoint_name = self._get_endpoint_name(name)
        print("Create endpoint with name:", endpoint_name)
        integration_name = self._get_integration_name(name)

        # Create backend for this topic.
        source_backend = KamelBackend(self.client, self.mode, topic=topic)

        # Create endpoint.
        source_backend.createProxyEndpoint(self.client, endpoint_name, route,
                                           integration_name)

        if self.camel_mode.isCluster():
            server_pod_name = utils.get_server_pod_name()

        # Endpoint address.
        endpoint_address = self.camel_mode.getQuarkusHTTPServer(
            server_pod_name, source=True)
        print("endpoint_address", endpoint_address)
        integration_content = [{
            'from': {
                'uri': f'timer:tick?period={period}',
                'steps': [{
                    'to': source_url
                }, {
                    'to': f'{endpoint_address}{route}'
                }]
            }
        }]

        # Start running the source integration.
        source_invocation = kamel.run([integration_content],
                                      self.mode,
                                      integration_name,
                                      integration_as_files=False)
        self.invocations.append(source_invocation)

    def add_sink(self, name, topic, sink):
        if sink['kind'] is None:
            raise TypeError('A Camel sink needs a kind.')
        if sink['kind'] not in ['slack-sink']:
            raise TypeError('Unsupported Camel sink.')
        channel = sink['channel']
        webhookUrl = sink['webhookUrl']
        route = sink['route']

        # Create backend if one hasn't been created so far.
        if self.kamel_backend is None:
            self.kamel_backend = KamelBackend(self.client, self.mode)

        # Write integration code to file.
        # TODO: for now only support 1 integration content.
        integration_content = [{
            'from': {
                'uri': f'platform-http:{route}',
                'steps': [{
                    'to': f'slack:{channel}?webhookUrl={webhookUrl}',
                }]
            }
        }]

        # Start running the integration.
        print("Start kamel run. Mode is cluster = ", self.mode.isCluster())
        integration_name = self._get_integration_name(name)
        sink_invocation = kamel.run([integration_content],
                                    self.mode,
                                    integration_name,
                                    integration_as_files=False)
        print("Append invocation to list.")
        self.invocations.append(sink_invocation)

        endpoint_name = self._get_endpoint_name(name)
        print("Create endpoint with name:", endpoint_name)
        self.kamel_backend.createProxyEndpoint(self.client, endpoint_name,
                                               route, integration_name)

        print("Add endpoint to Topic list.")
        helper = EndpointHelper.remote(self.kamel_backend,
                                       self.client.get_handle(endpoint_name),
                                       endpoint_name)
        topic.send_to.remote(helper, name)

    def exit(self):
        # TODO: delete endpoints.
        # This deletes all the integrations.
        for invocation in self.invocations:
            if self.mode.isCluster() or self.mode.isMixed():
                kamel.delete(invocation)
            elif self.mode.isLocal():
                invocation.kill.remote()
            else:
                raise RuntimeError("Unreachable")
        # TODO: check that the invocation does not need to be killed when
        # running in the Cluster or Mixed modes.

    def _get_endpoint_name(self, name):
        self.endpoint_id += 1
        return "_".join(["endpoint", name, str(self.endpoint_id)])

    def _get_integration_name(self, name):
        self.integration_id += 1
        return "-".join(["integration", name, str(self.integration_id)])


@ray.remote(num_cpus=0)
class EndpointHelper:
    def __init__(self, backend, endpoint_handle, endpoint_name):
        self.backend = backend
        self.endpoint_name = endpoint_name
        self.endpoint_handle = endpoint_handle

    def ingest(self, data):
        print("Endpoint:", self.endpoint_name, "DATA:", data)
        print("Data is not None", data is not None)
        if data is not None:
            answer = self.backend.postToProxyEndpointHandle(
                self.endpoint_handle, self.endpoint_name, data)
            print(answer)
