import argparse
import re

import yaml


def update_keystone(input_file):

    keystone = {}
    options = input_file["applications"]["keystone"]["options"]

    for key, value in options.items():
        key = key.replace("_", "-")
        keystone[key] = value
    return keystone


def update_nbi(input_file):

    nbi = {}
    options = input_file["applications"]["nbi"]["options"]

    for key, value in options.items():
        if key == "site_url":
            nbi["external-hostname"] = re.sub("https://|http://", "", value)
        elif key in (
            "mongodb_uri",
            "auth_backend",
            "security_context",
            "ingress_class",
        ):
            pass
        else:
            key = key.replace("_", "-")
            nbi[key] = value
    return nbi


def update_lcm(input_file):

    lcm = {}
    options = input_file["applications"]["lcm"]["options"]

    for key, value in options.items():
        if key in (
            "database_commonkey",
            "log_level",
        ):
            key = key.replace("_", "-")
            lcm[key] = value
        elif key == "vca_helm_ca_certs":
            lcm["helm-ca-certs"] = value
        elif key == "vca_stablerepourl":
            lcm["helm-stable-repo-url"] = value
    return lcm


def update_mon(input_file):

    mon = {}
    options = input_file["applications"]["mon"]["options"]

    for key, value in options.items():
        if key in (
            "security_context",
            "mongodb_uri",
        ) or key.startswith("vca_"):
            pass
        else:
            key = key.replace("_", "-")
            mon[key] = value
    return mon


def update_pol(input_file):

    pol = {}
    options = input_file["applications"]["pol"]["options"]

    for key, value in options.items():
        if key in ("mongodb_uri"):
            pass
        else:
            key = key.replace("_", "-")
            pol[key] = value
    return pol


def update_ro(input_file):

    ro = {}
    options = input_file["applications"]["ro"]["options"]

    for key, value in options.items():
        if key in ("mongodb_uri", "security_context"):
            pass
        else:
            key = key.replace("_", "-")
            ro[key] = value
    return ro


def update_ngui(input_file):

    ng_ui = {}
    options = input_file["applications"]["ng-ui"]["options"]

    for key, value in options.items():
        if key == "site_url":
            ng_ui["external-hostname"] = re.sub("https://|http://", "", value)
        elif key == "ingress_class":
            pass
        else:
            key = key.replace("_", "-")
            ng_ui[key] = value
    return ng_ui


def _get_controller_input(data):
    controller_info = data["controllers"]["osm-vca"]
    return controller_info


def _return_config_files(input_file, controller=False):
    with open(input_file, "r") as input:
        controllers_data = yaml.safe_load(input)
        controller_data = {
            "controllers": {"osm-vca": _get_controller_input(controllers_data)},
        }
        if controller:
            controller_data["current-controller"] = "osm-vca"

    return yaml.safe_dump(controller_data)


def mongodbintegrator(input_file):
    mongo = {}
    options = input_file["applications"]["lcm"]["options"]
    if options.get("mongodb_uri"):
        mongo["mongodb-uri"] = options["mongodb_uri"]

    return mongo


def ingressintegrator(input_file):
    ingress = {}
    options_nbi = input_file["applications"]["nbi"]["options"]
    options_ngui = input_file["applications"]["ng-ui"]["options"]

    if (
        options_nbi.get("ingress_class")
        and options_ngui.get("ingress_class")
        and options_nbi["ingress_class"] == options_ngui["ingress_class"]
    ):
        ingress["ingress-class"] = options_nbi["ingress_class"]

    return ingress


def vcaintegrator(input_file):
    vca = {}
    model_config = {}
    options = input_file["applications"]["lcm"]["options"]

    for key, value in options.items():
        if key == "vca_cloud":
            vca["lxd-cloud"] = value
        elif key == "vca_k8s_cloud":
            vca["k8s-cloud"] = value
        elif key.startswith("vca_model_config_"):
            key = key.replace("vca_model_config_", "")
            key = key.replace("_", "-")
            model_config[key] = value

    vca["model-configs"] = yaml.safe_dump(model_config)

    return vca


def add_accounts_controllers_info(accounts_file, controllers_file, public_key):
    vca = {}

    vca["accounts"] = _return_config_files(accounts_file)
    vca["controllers"] = _return_config_files(controllers_file, True)
    with open(public_key, "r") as pkey:
        vca["public-key"] = pkey.read()
    return vca


def parse_module(config, data):
    parsed_data = {"applications": {}}

    if MODULES.get(config["module"]):
        parsed_data["applications"][config["module"]] = {}
        parsed_data["applications"][config["module"]]["options"] = MODULES[
            config["module"]
        ](data)
    elif config["module"] == "keystone":
        parsed_data["applications"]["keystone"] = {}
        parsed_data["applications"]["keystone"]["options"] = update_keystone(data)
    else:
        parsed_data["applications"]["vca-integrator"] = {}
        parsed_data["applications"]["vca-integrator"]["options"] = vcaintegrator(data)
    return parsed_data


def parse_all(data):
    parsed_data = {"applications": {}}

    for module, function in MODULES.items():
        parsed_data["applications"][module] = {"options": function(data)}
    for module in NO_CHANGE_MODULES:
        if data["applications"][module].get("options"):
            parsed_data["applications"][module] = {
                "options": data["applications"][module]["options"]
            }
    parsed_data["applications"]["mongodb-integrator"] = {
        "options": mongodbintegrator(data)
    }
    return parsed_data


def set_accounts(config, data):

    if not data.get("applications"):
        data["applications"] = {"vca-integrator": {"options": {}}}
    if not data["applications"].get("vca-integrator"):
        data["applications"]["vca-integrator"] = {"options": {}}
    accounts_file = config["set_acc"][0]
    controllers_file = config["set_acc"][1]
    pkey_file = config["set_acc"][2]
    data["applications"]["vca-integrator"]["options"].update(
        add_accounts_controllers_info(accounts_file, controllers_file, pkey_file)
    )

    return data


MODULES = {
    "nbi": update_nbi,
    "lcm": update_lcm,
    "mon": update_mon,
    "pol": update_pol,
    "ro": update_ro,
    "ng-ui": update_ngui,
    "vca-integrator": vcaintegrator,
}

NO_CHANGE_MODULES = [
    "grafana",
    "prometheus",
    "kafka",
    "zookeeper",
]


def main():
    parser = argparse.ArgumentParser(
        description="Parse configuration from old Charms to be used by new ones",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group()
    parser.add_argument("input_config", help="Input configuration file")
    group.add_argument(
        "-s",
        "--set_acc",
        nargs=3,
        help="Add the configuration for accounts and controllers. \
            The way to call the script will be: \
            python3 parse_osm_config.py <output-config-file> -s <accounts-file.yaml> <controllers-file.yaml> <juju-public-key>",
    )

    group.add_argument(
        "-m",
        "--module",
        choices=[
            "nbi",
            "lcm",
            "mon",
            "pol",
            "ro",
            "ng-ui",
            "vca-integrator",
            "keystone",
        ],
        help="The config of the module will be written. Allowed module names are: nbi lcm mon pol ro ng-ui keystone and vca",
    )
    args = parser.parse_args()
    config = vars(args)

    all_modules = False if config.get("module") or config.get("set_acc") else True

    with open(config["input_config"], "r") as f:
        data = yaml.safe_load(f)
        if config.get("module"):
            parsed_data = parse_module(config, data)
            with open(f"{config['module']}-config.yaml", "w") as osm_config:
                osm_config.write(yaml.safe_dump(parsed_data))
        if config.get("set_acc"):
            updated_data = set_accounts(config, data)
            with open("osm-config.yaml", "w") as osm_config:
                osm_config.write(yaml.safe_dump(updated_data))
        if all_modules:
            parsed_data = parse_all(data)
            with open("osm-config.yaml", "w") as osm_config:
                osm_config.write(yaml.safe_dump(parsed_data))


if __name__ == "__main__":
    main()
