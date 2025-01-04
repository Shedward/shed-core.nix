
{ config, lib, pkgs, ... }:

{
  nixpkgs.config.allowUnfree = true;

  imports = [
    ./hardware-configuration.nix
    ./common
    ./machines/shed-core

    ./features/torrents
    ./features/dns
    ./features/home-tools
    ./features/plex
  ];

  system = {
    copySystemConfiguration = true;
    stateVersion = "23.11"; # Keep it!
  };
}
