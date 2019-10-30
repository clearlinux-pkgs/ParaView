#!/usr/bin/env python3

import configparser
import os
import subprocess
import shutil
import sys


def git_clone(repo, tag):
    subprocess.run(f"git clone --recursive {repo} -b {tag}".split(),
                   check=True)


def get_path_urls(package):
    path_urls = ""
    try:
        proc = subprocess.run(f"git -C {package} submodule status".split(),
                              check=True, capture_output=True)
        for line in proc.stdout.decode('utf-8').splitlines():
            sha, path, _ = line.split()
            subm = os.path.join(package, path)
            path_urls = get_path_urls(subm) + path_urls
            cmd = f"git -C {subm} remote get-url origin".split()
            uproc = subprocess.run(cmd, check=True, capture_output=True)
            url = uproc.stdout.decode('utf-8').strip()
            if url[-4:] == ".git":
                url = url[:-4]
            dirname = os.path.basename(url)
            commit_url = url + F"/-/archive/{sha}/{dirname}-{sha}.tar.bz2"
            if os.path.split(package)[0]:
                path_urls = f"{commit_url} {subm.split('/', maxsplit=1)[1]} " + path_urls
            else:
                head_tail = os.path.split(path)
                if not head_tail[0]:
                    path_urls = f"{commit_url} {head_tail[1]} " + path_urls
                else:
                    path_urls = f"{commit_url} {head_tail[0]} " + path_urls
            if not os.path.isfile(f"{sha}.tar.bz2"):
                subprocess.run(f"curl -L -O {commit_url}".split())
    except Exception as e:
        print(f"unable to get submodule details for {package}: {e}")
        sys.exit(1)

    return path_urls


def fixup_makefile(package, tag):
    path_urls = get_path_urls(package).strip()
    mcontent = []
    with open("Makefile", "r") as mfile:
        mcontent = mfile.readlines()
    for idx, line in enumerate(mcontent):
        if line.startswith("ARCHIVES"):
            vs = tag.split('.')
            major_version = vs[0] + '.' + vs[1]
            mcontent[idx] = f"ARCHIVES = http://www.paraview.org/files/{major_version}/ParaViewData-{tag}.tar.gz DataPackage {path_urls}\n"
            break
    with open("Makefile", "w") as mfile:
        mfile.writelines(mcontent)


def setup_archives(tag):
    conf = configparser.ConfigParser()
    try:
        conf.read("options.conf")
        if not os.path.isfile(os.path.join(conf['package']['name'], f".git/refs/heads/{tag}")):
            shutil.rmtree(conf['package']['name'], ignore_errors=True)
            git_clone(conf["package"]["giturl"], tag)
    except Exception as e:
        print(f"unable to grab submodule archives: {e}")
        sys.exit(1)
    fixup_makefile(conf["package"]["name"], tag)


def main():
    if len(sys.argv) != 2:
        print("Please provide tag to checkout")
        sys.exit(1)
    setup_archives(sys.argv[1])


if __name__ == '__main__':
    main()
