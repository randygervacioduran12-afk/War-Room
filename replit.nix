{ pkgs }: {
  deps = [
    pkgs.nano-wallet
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.postgresql
  ];
}