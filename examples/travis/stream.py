import ray
import rayvens

ray.init(address='auto')

client = rayvens.Client()

stream = client.create_stream('example')


def handler1(event):
    print('handler1 received', event)


def handler2(event):
    print('handler2 received', event)


stream >> handler1
stream >> handler2

for i in range(10):
    stream << f'event {i}'
