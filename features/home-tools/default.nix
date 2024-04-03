{ pkgs, ... }:

{
  environment = {
    systemPackages = with pkgs; [
      libz
      stdenv.cc.cc.lib
      (
        import ./home-tools-package.nix { 
          inherit pkgs stdenv;
          version = "0.0.2.6";
        }
      )
    ];
  };

  networking.firewall = {
    allowedTCPPorts = [8080];
    allowedUDPPorts = [8080];
  };
}