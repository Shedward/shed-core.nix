{ pkgs, ... }:

let
  port = "8080";
  home-tool-package = import ./home-tools-package.nix {
    inherit pkgs;
    version = "0.0.6.4";
    hash = "sha256-gkN8ZhF46Vzf1BYzTF+BgUoW8oDR+Ipke788qppRxaM=";
  };
  www = "${home-tool-package.outPath}/www";
in
{
  environment = {
    systemPackages = with pkgs; [
      libz
      stdenv.cc.cc.lib
      home-tool-package
    ];
  };

  networking.firewall = {
    allowedTCPPorts = [ 80 433 ];
  };

  users = {
    groups.home-tools = {};
    users.home-tools = {
      isSystemUser = true;
      group = "home-tools";
    };
  };

  systemd.services.home-tools = {
    enable = true;
    description = "Personal home services";
    unitConfig = {
      After = "network.target";
    };
    serviceConfig = {
      Type = "simple";
      WorkingDirectory = www;
      ExecStart = "${home-tool-package.outPath}/bin/HomeTools";
      User = "home-tools";
      Group = "home-tools";
      Restart = "always";
      RestartSec = 3;
      SyslogIdentifier = "home-tools";
      Environment = "HOME_TOOLS_CONFIG_PATH=/var/lib/home-tools/config.json";
    };
    wantedBy = [ "multi-user.target" ];
  };

  services.nginx = {
    enable = true;
    virtualHosts."home.home" = {
      locations = {

        # We deliver public resources directly with nginx
        "/(fonts|styles)/" = {
          root = "${www}/Public";
        };

        # Main page
        "/" = {
          proxyPass = "http://localhost:${port}";
          extraConfig = ''
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          '';
        };
      };
    };
  };
}
