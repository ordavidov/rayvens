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

import ray
from ray import serve

from rayvens.core.camel_anywhere import kamel
from rayvens.core.camel_anywhere.mode import mode, RayKamelExecLocation
from rayvens.core.camel_anywhere import kubernetes
from rayvens.core.camel_anywhere.tests import slack_sink_common

ray.init(num_cpus=4)
client = serve.start()
route = "/toslack"
message = "While Ray runs locally, use the kamel operator in a kind cluster to"
"print this to a kamel Slack sink."

mode.location = RayKamelExecLocation.MIXED

#
# Install kamel operator in the kind cluster created using the script
# in kamel subdirectory.
#

# kamelImage = "docker.io/apache/camel-k:1.3.1"
# publishRegistry = "registry:5000"
# installInvocation = kamel.install(kamelImage,
#                                   publishRegistry,
#                                   localCluster=True,
#                                   usingKind=True,
#                                   insecureRegistry=True)

#
# Use kamel run to create the slack sink using the kamel operator.
#
# print("Length of active pod list after install: ",
#       kubernetes.getNumActivePods())
# print("Name of install pod is", kubernetes.getPodName(installInvocation))

# List of environment variables to be used from current environment.
envVars = ["SLACK_WEBHOOK"]
integrationFiles = ["kamel/slack.yaml"]
integration_name = "my-simple-integration"

# Note: careful with the names, for pod names, the integration name will be
# modified by kamel to replace underscores with dashes.
runInvocation = kamel.run(integrationFiles,
                          mode,
                          integration_name,
                          envVars=envVars,
                          await_start=True)

#
# Create service through which we can communicate with the kamel sink.
# The port of the service must be one of the ports externalized by the cluster.
# This is only required when the communication with the sink happen from
# outside the cluster.
#
serviceName = "kind-external-connector"
kubernetes.createExternalServiceForKamel(mode, serviceName, integration_name)

#
# Start doing some work
#
slack_sink_common.sendMessageToSlackSink(client, message, route,
                                         integration_name)

#
# Stop kubectl service for externalizing the sink listener.
#
kubernetes.deleteService(mode, serviceName)

#
# Stop kamel sink.
#
kamel.delete(runInvocation, integration_name)

#
# Uinstall the kamel operator from the cluster.
#
# kamel.uninstall(installInvocation)
