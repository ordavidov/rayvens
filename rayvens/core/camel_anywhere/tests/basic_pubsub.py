#
# Copyright IBM Corporation 2021
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from rayvens.core.camel_anywhere import topics
import ray
ray.init()

# Import events.

# Set up subscriber responder.


def subscribeResponse():
    print("Hello publisher!")


# Create a topic as an actor.
newTopicHandle = topics.EventTopic.remote("newTopic")

# Add method as responder to any publication.
newTopicHandle.subscribe.remote(subscribeResponse)

# Print out the state of the EventTopic actor.
newTopicHandle.describe.remote()

# Publish with no arguments.
for i in range(10):
    newTopicHandle.publish.remote()
