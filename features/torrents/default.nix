
{ config, lib, pkgs, ... }:

{
  environment = {
    systemPackages = with pkgs; [
      transmission
    ];
  };

  networking.firewall.allowedTCPPorts = [
    9091
  ];

  services = {
    samba-wsdd = {
      enable = true;
      openFirewall = true;
    };

    samba = {
      enable = true;
      securityType = "user";
      openFirewall = true;

      extraConfig = ''
        workgroup = WORKGROUP
        security = user
        hosts allow = 192.168.44.
        guest account = nobody
        map to guest = bad user
      '';

      shares = {
        downloads = {
          path = "/home/shed/Downloads";
          browseable = "yes";
          "read only" = "no";
          "guest ok" = "no";
          "create mask" = "0644";
          "direcotry mask" = "0755";
        };
      };
    };

    transmission = {
      enable = true;
      openFirewall = true;
      user = "shed";
      settings = {
        download-dir = "/home/shed/Downloads";
        rpc-bind-address = "0.0.0.0";
        rpc-whitelist = "127.0.0.1,192.168.44.*";
      };
    };

    nginx = {
      enable = true;
      virtualHosts."home.home" = {
        locations = {
          "/torrents/" = { 
            proxyPass = "http://localhost:9091";
          };

          "/transmission/" = { 
            proxyPass = "http://localhost:9091";
          };
        };
      };
    };
  };
}
