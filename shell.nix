{
  pkgs ? import <nixpkgs> { },
}:

let
  python = pkgs.python313.withPackages (
    ps: with ps; [
      # runtime
      aiohttp
      attrs
      defusedxml
      # tests
      black
      flake8
      pylint
      pytest
      pytest-asyncio
      pytest-vcr
      syrupy
    ]
  );
in
pkgs.mkShell {
  packages = [ python ];
  shellHook = ''
    export PYTHONPATH="$PWD:$PYTHONPATH"
  '';
}
