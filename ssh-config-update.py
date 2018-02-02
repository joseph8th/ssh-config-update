#!/usr/bin/env python3

import os, sys
import boto3
import pprint as pp
from collections import OrderedDict


def get_aws_configs(user, pem_path):
    client = boto3.client('ec2')
    result = client.describe_instances()

    configs = OrderedDict()
    for ec2 in result["Reservations"]:
        for instance in ec2["Instances"]:
            public_ip = instance.get("PublicIpAddress", None)
            private_ip = instance.get("PrivateIpAddress", None)
            if not public_ip and not private_ip: continue

            names = [t["Value"] for t in instance["Tags"] if t["Key"] == "Name"]
            if not names: continue
            host = names[0].lower().replace("/", "_")

            key_name = instance.get("KeyName", None)
            if not key_name: continue

            key_path = os.path.join(pem_path, "{}.pem".format(key_name))
            if not os.path.exists(key_path): continue

            configs[host] = OrderedDict([
                ("Host", host),
                ("HostName", public_ip or private_ip),
                ("User", user),
                ("IdentityFile", key_path),
            ])

    return configs


def read_ssh_configs(ssh_config_path):
    if not os.path.exists(ssh_config_path):
        return []

    with open(ssh_config_path, 'r') as f:
        lines = f.readlines()

    configs = OrderedDict()
    config = OrderedDict()
    for line in lines:
        items = line.strip().split()
        if not items:
            configs[config["Host"]] = config
            config = OrderedDict()
            continue

        config[items[0]] = items[1]

    return configs


def write_ssh_configs(ssh_config_path, ssh_configs):
    with open(ssh_config_path, 'w') as f:
        for config in ssh_configs.values():
            lines = [' '.join([k,v]) for k,v in config.items()]
            for line in lines:
                f.write(line + "\n")
            f.write("\n")


def main():
    user = "ubuntu"
    home = os.path.expanduser("~")
    pem_path = os.path.join(home, ".aws")
    aws_configs = get_aws_configs(user, pem_path)

    # TODO
    pp.pprint(aws_configs)
    print("----")

    ssh_config_path = os.path.join(home, ".ssh", "config")
    ssh_configs = read_ssh_configs(ssh_config_path)

    # TODO
    pp.pprint(ssh_configs)
    print("----")

    for host, config in aws_configs.items():
        if host in ssh_configs:
            ssh_configs[host]["HostName"] = config["HostName"]
            ssh_configs[host]["IdentityFile"] = config["IdentityFile"]
        else:
            ssh_configs[host] = config

    # TODO
    pp.pprint(ssh_configs)

    write_ssh_configs(ssh_config_path, ssh_configs)


if __name__ == "__main__":
    sys.exit(main())
