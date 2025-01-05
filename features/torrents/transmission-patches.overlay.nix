self: super: {
  transmission_4 = super.transmission_4.overrideAttrs (oldAttrs: rec {
    patches = oldAttrs.patches or [] ++ [
      ((import super.path {}).fetchpatch2 {
        url = "https://gist.githubusercontent.com/Shedward/4dc8c211ce57501520802b3a3753ad86/raw/b13cc45ea6bde6dfe250fbf601e814ea00b099dd/transmission-announce-hack.patch";
        sha256 = "00pqb23mia9zdkp4cgqwxnbqg4swjb7r8jsqbsl56qwjb2l0c7c7";
      })
    ];
  });
}
