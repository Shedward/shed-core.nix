
{ config, lib, pkgs, ... }:

{
  services.plex = {
    enable = true;
    openFirewall = true;
    user="shed";
  };

  services.nginx = {
    enable = true;
    virtualHosts."plex.home" = {
      locations = {
        "/" = {
          proxyPass = "http://localhost:32400";
        };
      };
    };
  };
}
