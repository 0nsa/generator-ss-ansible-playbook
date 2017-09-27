#!/usr/bin/env python

import os

import yaml


def get_cfg_yaml_path():
    return os.path.realpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "cfg.yml"))


def get_servers_yaml_path(cfg):
    return os.path.realpath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", cfg["servers_yml_path"]))


def get_val(dct, key, default_value):
    if key in dct and dct[key] is not None:
        return dct[key]
    return default_value


def normalize_servers(data):
    ret = {}
    for env_name, env_data in data.items():
        ret[env_name] = {"sub_groups": {}, "groups": {}}
        if env_data is None:
            continue
        for group_name, group_data in get_val(env_data, "<sub_groups>", {}).items():
            if group_data is None:
                ret[env_name]["sub_groups"][group_name] = {"hosts": [], "vars": {}, "children": []}
                continue
            ret[env_name]["sub_groups"][group_name] = {
                "hosts": get_val(group_data, "hosts", []),
                "vars": get_val(group_data, "vars", {}),
                "children": get_val(group_data, "children", []),
            }
        for group_name, group_data in env_data.items():
            if group_name == "<sub_groups>":
                continue
            if group_data is None:
                ret[env_name]["groups"][group_name] = {
                    "hosts": {}, "vars": {}, "children": []}
                continue
            hosts = {}
            for idx, host_var in get_val(group_data, "hosts", {}).items():
                hosts[idx] = {} if host_var is None else host_var
            ret[env_name]["groups"][group_name] = {
                "hosts": hosts,
                "vars": get_val(group_data, "vars", {}),
                "children": get_val(group_data, "children", []),
            }
    return ret


def conv_inventories(data, env):
    hostvars = {}
    ret = {"_meta": {"hostvars": hostvars}}
    env_data = data[env]
    for group_name, group_data in env_data["sub_groups"].items():
        ret[group_name] = {
            "hosts": group_data["hosts"],
            "vars": group_data["vars"],
            "children": group_data["children"]}
    for group_name, group_data in env_data["groups"].items():
        hosts = []
        ret[group_name] = {
            "hosts": hosts,
            "vars": group_data["vars"],
            "children": group_data["children"]}
        for idx, hv in group_data["hosts"].items():
            host_id = "{}-{}.{}".format(group_name, idx, env)
            hostvar = {
                "idx": idx,
                "host_id": host_id}
            hostvar.update(hv)
            hostvars[host_id] = hostvar
            hosts.append(host_id)
    return ret


def read_cfg():
    with open(get_cfg_yaml_path()) as r:
        return yaml.load(r)


def read_data(cfg):
    with open(get_servers_yaml_path(cfg)) as r:
        return yaml.load(r)


def get_inventories():
    with open(get_cfg_yaml_path()) as r:
        cfg = yaml.load(r)
    with open(get_servers_yaml_path(cfg)) as r:
        servers = yaml.load(r)
    data = normalize_servers(servers)
    return dict(
        (env_name, conv_inventories(data, env_name))
        for env_name in data)
