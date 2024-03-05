
{ config, lib, pkgs, ... }:

{
  nix = {
    gc = {
      automatic = true;
      dates = "04:00";
    };
    settings = {
      experimental-features = ["nix-command" "flakes"];
    };
  };

  networking.firewall = {
    enable = true;
    allowPing = true;
  };

  services = {
    openssh.enable = true;
  };

  environment = {
    systemPackages = with pkgs; [
      git
      vim
      htop
      dig
    ];

    variables = {
      EDITOR = "vi";
    };
  };
}
