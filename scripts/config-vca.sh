VCA_OVERLAY=~/vca-overlay.yaml
K8S_CLOUD_NAME=microk8s
HOME=/home/$USER
CONTROLLER_NAME=$(juju controllers --format json | jq '.controllers | keys[]' | awk -F\" '{print $2}')
vca_user=$(cat $HOME/.local/share/juju/accounts.yaml | yq e .controllers.$CONTROLLER_NAME.user - )
vca_secret=$(cat $HOME/.local/share/juju/accounts.yaml | yq e .controllers.$CONTROLLER_NAME.password - )
vca_host=$(cat $HOME/.local/share/juju/controllers.yaml | yq e .controllers.$CONTROLLER_NAME.api-endpoints[0] - | cut -d ":" -f 1)
vca_port=$(cat $HOME/.local/share/juju/controllers.yaml | yq e .controllers.$CONTROLLER_NAME.api-endpoints[0] - | cut -d ":" -f 2)
vca_pubkey=\"$(cat $HOME/.local/share/juju/ssh/juju_id_rsa.pub)\"
vca_cloud="lxd-cloud"
vca_cacert=$(cat $HOME/.local/share/juju/controllers.yaml | yq e .controllers.$CONTROLLER_NAME.ca-cert - | base64 | tr -d \\n)

cat << EOF > $VCA_OVERLAY
applications:
  lcm:
    options:
      vca_user: $vca_user
      vca_secret: $vca_secret
      vca_host: $vca_host
      vca_port: $vca_port
      vca_pubkey: $vca_pubkey
      vca_cacert: $vca_cacert
      vca_cloud: $vca_cloud
      vca_k8s_cloud: $K8S_CLOUD_NAME
  mon:
    options:
      vca_user: $vca_user
      vca_secret: $vca_secret
      vca_host: $vca_host
      vca_cacert: $vca_cacert
EOF


