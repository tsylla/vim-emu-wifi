# Copyright (c) 2015 SONATA-NFV and Paderborn University
# ALL RIGHTS RESERVED.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).

# Forked and edited on 05-06/2022 to implement more functions by Gustave
# Eiffel University under EU 5GRail Project

from requests import get, put, delete
from tabulate import tabulate
import pprint
import argparse
from subprocess import Popen

pp = pprint.PrettyPrinter(indent=4)


class RestApiClient():
    def __init__(self):
        self.cmds = {}

    def execute_command(self, args):
        if getattr(self, args["command"]) is not None:
            # call the local method with the same name as the command arg
            getattr(self, args["command"])(args)
        else:
            print("Command not implemented.")

    def start(self, args):

        req = {'image': args.get("image"),
               'command': args.get("docker_command"),
               'network': args.get("network"),
               'environment': args.get("environment"),
               'volume': args.get("volume"),
               'cpu_shares': args.get("cpu_shares"),
               'cpu_period': args.get("cpu_period"),
               'cpu_quota': args.get("cpu_quota"),
               'mem_limit': args.get("mem_limit")}

        response = put("%s/restapi/compute/%s/%s" %
                       (args.get("endpoint"),
                        args.get("datacenter"),
                        args.get("name")),
                       json=req)

        pp.pprint(response.json())

    def stop(self, args):

        response = delete("%s/restapi/compute/%s/%s" %
                          (args.get("endpoint"),
                           args.get("datacenter"),
                           args.get("name")))
        pp.pprint(response.json())

    def move(self, args):
        req = {'destination':args.get("dest_datacenter")}
        response = put("%s/restapi/compute/%s/%s"%
                        (args.get("endpoint"),
                        args.get("datacenter"),
                        args.get("name")),json=req)

        pp.pprint(response.json())

    def list(self, args):

        list = get('%s/restapi/compute/%s' %
                   (args.get("endpoint"), args.get('datacenter'))).json()

        table = []
        for c in list:
            # for each container add a line to the output table
            if len(c) > 1:
                name = c[0]
                status = c[1]
                # eth0ip = status.get("docker_network", "-")
                netw_list = [netw_dict['intf_name']
                             for netw_dict in status.get("network")]
                dc_if_list = [netw_dict['dc_portname']
                              for netw_dict in status.get("network")]
                table.append([status.get("datacenter"),
                              name,
                              status.get("image"),
                              ','.join(netw_list),
                              ','.join(dc_if_list)])
                # status.get("state").get("Status")]

        headers = ["Datacenter",
                   "Container",
                   "Image",
                   "Interface list",
                   "Datacenter interfaces"]
        print(tabulate(table, headers=headers, tablefmt="grid"))

    def status(self, args):

        list = get("%s/restapi/compute/%s/%s" %
                   (args.get("endpoint"),
                    args.get("datacenter"),
                    args.get("name"))).json()

        pp.pprint(list)

    def xterm(self, args):
        vnf_names = args.get("vnf_names")
        for vnf_name in vnf_names:
            Popen(['xterm', '-xrm', 'XTerm.vt100.allowTitleOps: false', '-T', vnf_name,
                   '-e', "docker exec -it mn.{0} /bin/bash".format(vnf_name)])


parser = argparse.ArgumentParser(description="""son-emu-cli compute

    Examples:
    - son-emu-cli compute start -d dc2 -n client -i sonatanfv/sonata-iperf3-vnf
    - son-emu-cli compute start -d dc1 -n client -i sonatanfv/sonata-iperf3-vnf -v /home/wifi/db:/db
    - son-emu-cli list
    - son-emu-cli compute status -d dc2 -n client
    - son-emu-cli compute move -orig dc1 -dest dc3 -n client
    """, formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument(
    "command",
    choices=['start', 'stop', 'move', 'list', 'status', 'xterm'],
    help="Action to be executed.")
parser.add_argument(
    "vnf_names",
    nargs='*',
    help="vnf names to open an xterm for")
parser.add_argument(
    "--datacenter", "-d", dest="datacenter",
    help="Data center to which the command should be applied.")
        
parser.add_argument(
    "--origin", "-orig", dest="origin_datacenter",
    default="",
    help="Data center towards which the vnf will be moved, e.g 'dc1'")

parser.add_argument(
    "--destination", "-dest", dest="dest_datacenter",
    default="",
    help="Data center towards which the vnf will be moved, e.g 'dc3'")

parser.add_argument(
    "--name", "-n", dest="name",
    help="Name of compute instance e.g. 'vnf1'.")
parser.add_argument(
    "--image", "-i", dest="image",
    help="Name of container image to be used e.g. 'ubuntu:trusty'")
parser.add_argument(
    "--dcmd", "-c", dest="docker_command",
    help="Startup command of the container e.g. './start.sh'")

parser.add_argument(
    "--cpu-percent","-cpu", dest="cpu_percent", default=""
)
parser.add_argument(
    "--net", dest="network",
    help="Network properties of a compute instance e.g. \
          '(id=input,ip=10.0.10.3/24),(id=output,ip=10.0.10.4/24)' for multiple interfaces.")
parser.add_argument(
    "--endpoint", "-e", dest="endpoint",
    default="http://127.0.0.1:5001",
    help="REST API endpoint of son-emu (default:http://127.0.0.1:5001)")

parser.add_argument(
    "--environment",'-env', dest="environment",
    default=None,
    help="Host environment variable to use inside vnfs, e.g., IPERF_SERVER, IPERF_PORT and DB_SERVER.")

parser.add_argument(
    "--volume", "-v", dest="volume",
    default="",
    help="Docker volume to use within container using docker -v option"
)

parser.add_argument(
    "--cpu-share", "-cpu-share", dest="cpu_shares",
    default="",
    help="Specify the CPU Share to set the weight of the CPU used by the container. If not set, the default value is 1024."
)

parser.add_argument(
    "--cpu-period", "-cpu-p", dest="cpu_period",
    default="",
    help="Specify the CPU CFS scheduler period, which is used alongside --cpu-quota. Defaults to 100000 microseconds (100 milliseconds)."
)

parser.add_argument(
    "--cpu_quota", "-cpu-q", dest="cpu_quota",
    default="",
    help="Impose a CPU CFS quota on the container. The number of microseconds per --cpu-period that the container is limited to before throttled. "
)

parser.add_argument(
    "--mem-limit", "-mem", dest="mem_limit",
    default="",
    help="The maximum amount of memory the container can use."
)

def main(argv):
    args = vars(parser.parse_args(argv))
    c = RestApiClient()
    c.execute_command(args)
