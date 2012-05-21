#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Gregory Sitnin <sitnin@gmail.com>"
__copyright__ = "Gregory Sitnin, 2012"
__version__ = "0.2.1"

import os
import sys
import argparse
import re
import json
import shutil
import subprocess


def filename_matches(filename, matches):
    result = False
    for pattern in matches:
        p = "^" + pattern.replace('.', '\.').replace('*', '.*').replace('?', '.') + "$"
        if re.match(p, filename) is not None:
            result = True
    return result


def buildFilesList(directory, includes, excludes):
    files = set()
    l = len(directory) + 1
    for dirpath, dirnames, filenames in os.walk(directory, followlinks=True):
        for fn in filenames:
            short_filename = os.path.join(dirpath, fn)[l:]
            if filename_matches(short_filename, includes) and not filename_matches(short_filename, excludes):
                files.add(short_filename)
    return files


def _print(msg):
    if not args.quiet:
        print(msg)


def load_rules(filename):
    with open(filename, "r") as f:
        contents = f.read()
        f.close()
    return json.loads(contents)


def copy_chunk(src_dir, tgt_dir, includes, excludes):
    files = buildFilesList(src_dir, includes, excludes)
    for filename in files:
        target_filename = os.path.join(tgt_dir, filename)
        target_dir = os.path.dirname(target_filename)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        shutil.copy2(os.path.join(src_dir, filename), target_filename)
        shutil.copystat(os.path.join(src_dir, filename), target_filename)


def make_control_file(directory, defs):
    with open(os.path.join(directory, "control"), "w") as f:
        for key in defs:
            if defs[key]:
                f.write("%s: %s\n" % (key, defs[key]))
        f.close()


def make_conffiles_file(debian_dir, tmp_dir, tgt_dir, includes, excludes):
    with open(os.path.join(debian_dir, "conffiles"), "w") as f:
        files = buildFilesList(real_tmp + tgt_dir, includes, excludes)
        for filename in files:
            target_filename = os.path.join(tgt_dir, filename)
            f.write("%s\n" % target_filename)
        f.close()


def make_plain_conffiles(directory, defs):
    with open(os.path.join(directory, "conffiles"), "w") as f:
        for item in defs:
            f.write("%s\n" % item)
        f.close()


def make_debian_binary(directory):
    with open(os.path.join(directory, "debian-binary"), "w") as f:
        f.write("2.0")
        f.close()


def copy_scripts(debian_dir, src_dir, scripts):
    for key in scripts:
        if scripts[key]:
            target_filename = os.path.join(debian_dir, key)
            shutil.copy2(os.path.join(src_dir, scripts[key]), target_filename)
            os.chmod(target_filename, 0755)


def build_package(tmp_dir, package):
    os.chdir(tmp_dir)
    subprocess.check_call(["dpkg", "--build", package])
    # os.execl("/usr/bin/dpkg", "--build", package)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Dumb .deb builder', prog='ddb')
    arg_parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)

    arg_parser.add_argument('-r', '--rules', help='configuration file path', required=True)
    arg_parser.add_argument('-s', '--src', help='source directory', required=True)
    arg_parser.add_argument('-t', '--tmp', help='temp directory', required=True)
    arg_parser.add_argument('-o', '--out', help='output directory', required=True)

    arg_parser.add_argument('-p', '--package', help='package file name')
    arg_parser.add_argument('-d', '--debian', help='debian package version')
    arg_parser.add_argument('-u', '--ubuntu', help='ubuntu package version')

    arg_parser.add_argument('-f', '--force', help='force directory operations', action="store_true")
    arg_parser.add_argument('-q', '--quiet', help='quiet execution (produce no output)', action="store_true")
    args = arg_parser.parse_args()

    rules_filename = os.path.abspath(args.rules)
    src_dir = os.path.abspath(args.src)
    tmp_dir = os.path.abspath(args.tmp)
    out_dir = os.path.abspath(args.out)
    if os.path.isfile(rules_filename):
        _print("Dumb .deb builder version %s (c) Gregory Sitnin, 2012.\n" % __version__)
        try:
            _print("Source: %s" % src_dir)
            if not os.path.exists(src_dir):
                os.makedirs(tmp_dir)

            _print("Output: %s" % out_dir)
            if not os.path.exists(out_dir):
                if args.force:
                    os.makedirs(out_dir)
                else:
                    raise Exception("Output directory must not exist")

            _print("Temp: %s" % tmp_dir)
            if os.path.exists(tmp_dir):
                if args.force:
                    shutil.rmtree(tmp_dir, True)
                else:
                    raise Exception("Temporary directory must not exist")

            _print("Rules file %s" % rules_filename)
            rules = load_rules(rules_filename)

            _print("")

            if args.package:
                deb_filename = args.package
            else:
                deb_filename = "%s_%s" % (rules["control"]["Package"], rules["control"]["Version"])

                if args.debian:
                    deb_filename = "%s-%s" % (deb_filename, args.debian)
                if args.ubuntu:
                    if not args.debian:
                        deb_filename += "-0"
                    deb_filename = "%subuntu%s" % (deb_filename, args.ubuntu)
                if args.debian or args.ubuntu:
                    deb_filename += "_" + rules["control"]["Architecture"]

            real_tmp = os.path.join(tmp_dir, deb_filename)

            _print("Copying files...")
            for chunk in rules["files"]:
                chunk_src_dir = os.path.join(src_dir, chunk["source"]) if "source" in chunk else src_dir
                includes = chunk["include"] if "include" in chunk else list()
                excludes = chunk["exclude"] if "exclude" in chunk else list()
                copy_chunk(chunk_src_dir, real_tmp + chunk["target"], includes, excludes)

            _print("Generating DEBIAN directory contents...")
            debian_dir = os.path.join(real_tmp, "DEBIAN")
            os.mkdir(debian_dir)

            make_control_file(debian_dir, rules["control"])

            if "conffiles" in rules:
                make_plain_conffiles(debian_dir, rules["conffiles"])
                # for chunk in rules["conffiles"]:
                #     make_conffiles_file(debian_dir, real_tmp, chunk["path"], chunk["files"], [])

            copy_scripts(debian_dir, src_dir, rules["scripts"])

            _print("Building package...")
            build_package(tmp_dir, deb_filename)

            _print("Building package...")
            src_deb_filename = os.path.join(tmp_dir, deb_filename + ".deb")
            out_deb_filename = os.path.join(out_dir, deb_filename + ".deb")
            shutil.copy2(src_deb_filename, out_deb_filename)

            _print("Deleting temporary directory...")
            shutil.rmtree(tmp_dir, True)

            _print("\nPackage built: %s" % out_deb_filename)
            sys.exit(0)
        except Exception, e:
            _print(unicode(e))
            sys.exit(1)
    else:
        _print("Cannot find rules file %s" % rules_filename)
        sys.exit(1)
