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

import os
from rayvens.core import kamel_utils
from rayvens.core.mode import mode


# Method to install kamel in a cluster.
# The cluster needs to be already started. An operator image, and a registry
# that Camel-K can use to publish newly created images to are needed.
def install(kamelImage,
            publishRegistry,
            mode=mode,
            localCluster=False,
            usingKind=False,
            insecureRegistry=False):
    # Enforce local cluster, for now.
    # TODO: make this work in an actual cluster.
    if not localCluster:
        raise RuntimeError('only local clusters are supported')

    # If running a local cluster (i.e. cluster running on local machine)
    # then only the kind cluster is supported.
    # TODO: enable this for other cluster types.
    if localCluster and not usingKind:
        raise RuntimeError('locally, only kind cluster is supported')

    command = ["install"]

    # Namespace
    command.append("-n")
    command.append(mode.namespace)

    # Add kamel operator image.
    command.append("--operator-image")
    command.append(kamelImage)

    # Add registry that kamel can use for image publication.
    command.append("--registry")

    # Kind cluster starts with a registry.
    if usingKind:
        command.append(publishRegistry)

    # Local registry used to publish newly constructed images is insecure.
    # TODO: support secure registries.
    if (insecureRegistry):
        command.append("--registry-insecure")

    # Force installation.
    command.append("--force")

    return kamel_utils.invoke_kamel_command(command, mode, "camel-k-operator")


# Invoke kamel uninstall.
def uninstall(install_invocation):
    command = ["uninstall"]

    # Namespace
    command.append("-n")
    command.append(install_invocation.mode.namespace)

    return kamel_utils.invoke_kamel_command(command, install_invocation.mode,
                                            "camel-k-operator")


# Kamel run invocation.
def run(integration_content, mode, integration_name, envVars=[]):
    command = ["run"]

    # Append ProcessFile.java file.
    process_file = os.path.join(os.path.dirname(__file__), 'ProcessFile.java')
    command.append(process_file)

    if mode.transport == 'http':
        # Append Queue.java file.
        queue = os.path.join(os.path.dirname(__file__), 'Queue.java')
        command.append(queue)

    # Integration name.
    command.append("--name")
    command.append(integration_name)

    # Namespace
    command.append("-n")
    command.append(mode.namespace)

    for envVar in envVars:
        if envVar not in os.environ:
            raise RuntimeError("Variable %s not set in current environment" %
                               envVar)
        command.append("--env")
        command.append("%s=%s" % (envVar, os.getenv(envVar)))

    return kamel_utils.invoke_kamel_command(
        command,
        mode,
        integration_name,
        integration_content=integration_content)


# Kamel local run invocation.
def local_run(integration_content,
              mode,
              integration_name,
              envVars=[],
              port=None):
    command = ["local", "run"]

    # Append ProcessFile.java file.
    process_file = os.path.join(os.path.dirname(__file__), 'ProcessFile.java')
    command.append(process_file)

    if mode.transport == 'http':
        # Append Queue.java file.
        queue = os.path.join(os.path.dirname(__file__), 'Queue.java')
        command.append(queue)

        # Port is mandatory.
        if port is None:
            return RuntimeError('port is missing')

        # In the case of HTTP, add the port:
        command.append('--property')
        command.append(f'quarkus.http.port={port}')

    return kamel_utils.invoke_kamel_command(
        command,
        mode,
        integration_name,
        integration_content=integration_content)


# Kamel log command (needs operator).
def log(mode, integration_name, custom_message):
    command = ["log"]

    # Add integration name.
    command.append(integration_name)

    # Namespace
    command.append("-n")
    command.append(mode.namespace)

    return kamel_utils.invoke_kamel_command(command,
                                            mode,
                                            integration_name,
                                            message=custom_message)


# Kamel delete invocation (needs operator).
def delete(integration_invocation, integration_name):
    # Compose command with integration name.
    command = ["delete"]

    # Namespace
    command.append("-n")
    command.append(integration_invocation.mode.namespace)

    command.append(integration_name)

    return kamel_utils.invoke_kamel_command(command,
                                            integration_invocation.mode,
                                            integration_name)
