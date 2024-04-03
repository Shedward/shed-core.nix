{ stdenv, pkgs, version }:

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
  ];

  nativeBuildInputs = [
    autoPatchelfHook
  ];

  src = fetchurl {
    url = "https://github.com/Shedward/home-tools/releases/download/v${version}/HomeTools.tar.gz";
    hash = "sha256-RVRHwWeaEMjYkMoSOLhL1ux5x/t7CkicjjnZKqoSUeM=";
  };

  sourceRoot = ".";
  installPhase = ''
    runHook preInstall
    ls -la
    install -m755 -D HomeTools/HomeTools $out/bin/HomeTools
    cp -r HomeTools/lib $out/lib
    runHook postInstall
  '';
}