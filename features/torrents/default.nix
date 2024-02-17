
{ config, lib, pkgs, ... }:

{
  environment = {
    systemPackages = with pkgs; [
      transmission
    ];
  };

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
        hosts allow = 192.168.88.
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
      user = "shed";
      settings = {
        download-dir = "/home/shed/Downloads";
      };
    };
  };
}
