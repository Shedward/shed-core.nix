
{ config, lib, pkgs, ... }:

{
  imports = [
    ./hardware-configuration.nix
    ./common
    ./machines/shed-core

    ./features/torrents
    ./features/dns
  ];

  system = {
    copySystemConfiguration = true;
    stateVersion = "23.11"; # Keep it!
  };
}
