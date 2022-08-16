# osm-upgrade-to-v12-tools
Different tools used to test the upgrade of OSM to v12

In the folder "bundles" there are a set bundles used in the internal upgrading guides to deploy OSM.

In the folder "images" there are a set of images used together with the bundles for the deployment of OSM.

The folder "scripts" has the tools that were used  during the upgrade procedure.

## Scripts

The following scripts are listed in this folder:

* parse_osm_config.py
* create-ingress-config.sh
* config-vca.sh
* configure-lxd-cloud.sh

Let's see the usage of each of them

### parse_osm_config.py

Use the “parse_osm_config.py” script to create the new configuration that we will use for in the new charms. “parse_osm_config.py” script needs the configuration of the old charms. With that information it can create the configuration for all modules except keystone because keystone is deployed separately of the rest of the charms.


```bash
python3 parse_osm_config.py -h
usage: parse_osm_config.py [-h] [-s SET_ACC SET_ACC SET_ACC] [-m MODULE] input_config

Parse configuration from old Charms to be used by new ones

positional arguments:
  input_config          Input configuration file

optional arguments:
  -h, --help            show this help message and exit
  -s SET_ACC SET_ACC SET_ACC, --set_acc SET_ACC SET_ACC SET_ACC
                        Add the configuration for accounts and controllers. The way to call the script will be: python3 parse_osm_config.py <output-
                        config-file> -s <accounts-file.yaml> <controllers-file.yaml> <juju-public-key> (default: None)
  -m MODULE, --module MODULE
                        The config of the module will be written. Allowed module names are: nbi lcm mon pol ro ng-ui keystone and vca (default: None)
```

To get the configuration for Keystone charm, we can use the option `-m <module_name>` (in this case `module_name=keystone`). That will create the configuration just for that module:

```
python3 parse_osm_config.py ./osm-bundle.yaml -m keystone
```

Finally, we can add the configuration for Juju accounts and Juju controllers. For that, we need to specify the Juju accounts and Juju controllers files, that can be found under the “/home/<user>/.local/share/juju” folder.

```
python3 parse_osm_config.py osm-config.yaml -s ~/.local/share/juju/accounts.yaml ~/.local/share/juju/controllers.yaml ~/.local/share/juju/ssh/juju_id_rsa.pub
```
