
{ config, lib, pkgs, ... }:

{
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
            "\"nuc.shed A 192.168.88.23\""
            "\"router1.shed A 192.168.88.1\""
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
