
{ config, lib, pkgs, ... }:

{
  nixpkgs.overlays = [
    (import ./transmission-patches.overlay.nix)
  ];

  environment = {
    systemPackages = with pkgs; [
      transmission_4
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
      openFirewall = true;

      settings = {
        global = {
          workgroup = "WORKGROUP";
          "hosts allow" = "192.168.88.";
          "guest account" = "nobody";
          "map to guest" = "bad user";
        };

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
        rpc-whitelist = "127.0.0.1,192.168.88.*";
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
