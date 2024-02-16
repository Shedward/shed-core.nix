# Edit this configuration file to define what should be installed on
# your system. Help is available in the configuration.nix(5) man page, on
# https://search.nixos.org/options and in the NixOS manual (`nixos-help`).

{ config, lib, pkgs, ... }:

{
  imports = [
    ./hardware-configuration.nix
  ];

  nix.settings = {
    experimental-features = ["nix-command" "flakes"];
  };

  boot.loader = {
    systemd-boot.enable = true;
    efi.canTouchEfiVariables = true;
  };

  networking = {
    hostName = "shed-core";

    firewall = {
      enable = true;
      allowPing = true;
    };
  };

  environment = {
    systemPackages = with pkgs; [
      git
      vim
      htop
      transmission
    ];

    variables = {
      EDITOR = "vi";
    };
  };

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

  services = {
    openssh.enable = true;

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

  system = {
    copySystemConfiguration = true;
    stateVersion = "23.11"; # Keep it!
  };

  powerManagement.cpuFreqGovernor = "powersave";
}
