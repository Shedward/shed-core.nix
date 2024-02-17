
{ config, lib, pkgs, ... }:

{
  boot.loader = {
    systemd-boot.enable = true;
    efi.canTouchEfiVariables = true;
  };

  networking.hostName = "shed-core";
  time.timeZone = "Europe/Moscow";

  users.users = {
    shed = {
      description = "Vlad Maltsev";
      isNormalUser = true;
      extraGroups = [
        "wheel" "disk" "systemd-journal" "transmission"
      ];
    };
  };

  powerManagement.cpuFreqGovernor = "powersave";
}
