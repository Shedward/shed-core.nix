
{ config, lib, pkgs, ... }:

let
  adblockLocalZones = pkgs.stdenv.mkDerivation {
    name = "unbound-zones-adblock";

    src = (pkgs.fetchFromGitHub {
      owner = "StevenBlack";
      repo = "hosts";
      rev = "3.14.53";
      sha256 = "sha256-Z6Kz4bRtswzoZt4xroSWfSZKMM+fWpsVQMI+Cy7EfVE=";
    } + "/hosts");

    phases = [ "installPhase" ];
    installPhase = ''
      ${pkgs.gawk}/bin/awk '{sub(/\r$/,"")} {sub(/^127\.0\.0\.1/,"0.0.0.0")} BEGIN { OFS = "" } NF == 2 && $1 == "0.0.0.0" { print "local-zone: \"", $2, "\" refuse"}' $src | tr '[:upper:]' '[:lower:]' | sort -u >  $out
    '';
  };
in {
  networking.firewall = {
    allowedUDPPorts = [ 53 ];
    allowedTCPPorts = [ 53 ];
  };

  services = {
    unbound = {
      enable = true;

      settings = {
        server = {
          interface = [ "0.0.0.0" ];
          access-control = [
            "127.0.0.0/8 allow"
            "192.168.0.0/16 allow"
          ];
          private-address = [
            "192.168.0.0/16"
          ];
          local-data = [
            "\"home.home A 192.168.44.21\""
            "\"router1.home A 192.168.44.1\""
            "\"router2.home A 192.168.44.2\""
          ];
          include = [
            "${adblockLocalZones}"
          ];
        };
        forward-zone = [
            {
              name = ".";
              forward-tls-upstream = true;
              forward-addr = [
                "1.1.1.1@853#cloudflare-dns.com"
                "1.0.0.1@853#cloudflare-dns.com"
              ];
            }
        ];
      };
    };
  };
}
