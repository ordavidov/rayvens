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

from enum import Enum
from rayvens.core import utils


class RayvensMode(Enum):
    # Ray and Kamel running locally.
    LOCAL = 1

    # TODO: Remove this.
    LOCAL_LOCAL = 8

    # Ray running locally, Kamel local running in a container in the cluster.
    MIXED_LOCAL = 2

    # Ray running locally, Kamel operator running in the cluster.
    MIXED_OPERATOR = 3

    # Ray in cluster, Kamel local running in a container in the cluster.
    CLUSTER_LOCAL = 4

    # Ray in cluster, Kamel operator running in the cluster.
    CLUSTER_OPERATOR = 5

    # Ray operator in cluster, Kamel local running in a container in cluster.
    OPERATOR_LOCAL = 6

    # Ray operator in cluster, Kamel operator running in the cluster.
    OPERATOR_OPERATOR = 7


class RunMode:
    def __init__(self, run_mode=RayvensMode.LOCAL):
        self.run_mode = run_mode
        self.namespace = "ray"
        self.transport = None

    def setNamespace(self, namespace):
        self.namespace = namespace

    def getNamespace(self):
        return self.namespace

    def getQuarkusHTTPServer(self,
                             integration_name,
                             serve_source=False,
                             port=None):
        if self.run_mode == RayvensMode.LOCAL:
            if port is None:
                raise RuntimeError('port is not specified')
            return f'http://localhost:{port}'
        if self.run_mode == RayvensMode.LOCAL_LOCAL:
            return "http://0.0.0.0:8080"
        if self.run_mode == RayvensMode.MIXED_OPERATOR:
            return "http://localhost:%s" % utils.externalizedClusterPort
        if self.run_mode == RayvensMode.CLUSTER_OPERATOR:
            if integration_name == "":
                raise RuntimeError("integration name is not set")
            if serve_source:
                return "http://%s.%s.svc.cluster.local:%s" % (
                    integration_name, self.namespace,
                    utils.internalClusterPortForSource)
            return "http://%s.%s.svc.cluster.local:%s" % (
                integration_name, self.namespace, utils.internalClusterPort)
        raise RuntimeError("unreachable")

    def server_address(self, integration):
        return self.getQuarkusHTTPServer(integration.integration_name,
                                         port=integration.port)

    def isLocal(self):
        return self.run_mode == RayvensMode.LOCAL_LOCAL or \
            self.run_mode == RayvensMode.LOCAL

    def isMixed(self):
        return self.run_mode == RayvensMode.MIXED_OPERATOR

    def isCluster(self):
        return self.run_mode == RayvensMode.CLUSTER_OPERATOR


# Default execution mode.
mode = RunMode()
