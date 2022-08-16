externalhostname=$(ip a l dev ens3 | awk -F"inet " '$2 !~ /^$/ {print $2}' | awk -F\/ '{print $1}')

cat >ingress-options.yaml <<EOF
applications:
  nbi:
    options:
     external-hostname: "nbi.$externalhostname.nip.io"
  ng-ui:
    options:
     external-hostname: "ui.$externalhostname.nip.io"
  grafana:
    options:
      site_url: "http://grafana.$externalhostname.nip.io"
  prometheus:
    options:
      site_url: "http://prometheus.$externalhostname.nip.io"
EOF