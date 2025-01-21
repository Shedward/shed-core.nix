self: super: {
  transmission_4 = super.transmission_4.overrideAttrs (oldAttrs: rec {
    patches = oldAttrs.patches or [] ++ [
      ((import super.path {}).fetchpatch2 {
        url = "https://gist.githubusercontent.com/Shedward/4dc8c211ce57501520802b3a3753ad86/raw/b13cc45ea6bde6dfe250fbf601e814ea00b099dd/transmission-announce-hack.patch";
        sha256 = "sha256-PmFnCKmwiq/2hR9E2zLqdfikGa5d0fBPwqY2SamnrsA=";
      })
    ];
  });
}
