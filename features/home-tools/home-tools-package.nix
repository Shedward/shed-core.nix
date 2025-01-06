{ pkgs, version, hash }:

with pkgs; stdenv.mkDerivation rec {
  pname = "home-tools";
  inherit version;

  meta = with lib; {
    homepage = "https://github.com/Shedward/home-tools";
    description = "Personal home tools";
    platform = platforms.linux;
  };

  preBuild = ''
    addAutoPatchelfSearchPath HomeTools/lib
  '';

  buildInputs = [
    zlib
    stdenv.cc.cc.lib
    libtinfo
    libxml2
    curl
  ];

  nativeBuildInputs = [
    autoPatchelfHook
  ];

  src = fetchurl {
    url = "https://github.com/Shedward/home-tools/releases/download/v${version}/HomeTools.tar.gz";
    inherit hash;
  };

  sourceRoot = ".";
  installPhase = ''
    runHook preInstall
    install -m755 -D HomeTools $out/bin/HomeTools
    mkdir "$out/www"
    cp -r Resources "$out/www/"
    cp -r Public "$out/www/"
    cp -r lib "$out/lib"
    runHook postInstall
  '';
}
