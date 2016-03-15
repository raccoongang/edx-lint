"""The edx_lint write command."""

from __future__ import print_function

import os

import six
from six.moves import configparser
from six.moves import cStringIO

import pkg_resources

from edx_lint.tamper_evident import TamperEvidentFile
from edx_lint.configfile import merge_configs


WARNING_HEADER = """\
# ***************************
# ** DO NOT EDIT THIS FILE **
# ***************************
#
# This file was generated by edx-lint: http://github.com/edx.edx-lint
#
# If you want to change this file, you have two choices, depending on whether
# you want to make a local change that applies only to this repo, or whether
# you want to make a central change that applies to all repos using edx-lint.
#
# LOCAL CHANGE:
#
# 1. Edit the local {tweaks_name} file to add changes just to this
#    repo's file.
#
# 2. Run:
#
#       $ edx_lint write {filename}
#
# 3. This will modify the local file.  Submit a pull request to get it
#    checked in so that others will benefit.
#
#
# CENTRAL CHANGE:
#
# 1. Edit the {filename} file in the edx-lint repo at
#    https://github.com/edx/edx-lint/blob/master/edx_lint/files/{filename}
#
# 2. Make a new version of edx_lint, which involves the usual steps of
#    incrementing the version number, submitting and reviewing a pull
#    request, and updating the edx-lint version reference in this repo.
#
# 3. Install the newer version of edx-lint.
#
# 4. Run:
#
#       $ edx_lint write {filename}
#
# 5. This will modify the local file.  Submit a pull request to get it
#    checked in so that others will benefit.
#
#
#
#
#
# STAY AWAY FROM THIS FILE!
#
#
#
#
#
# SERIOUSLY.
#
# ------------------------------
"""

def write_main(argv):
    """
    write FILENAME
        Write a local copy of FILENAME using FILENAME_tweaks for local tweaks.
    """
    if len(argv) != 1:
        print("Please provide the name of a file to write.")
        return 1

    filename = argv[0]
    resource_name = "files/" + filename
    tweaks_name = amend_filename(filename, "_tweaks")

    if not pkg_resources.resource_exists("edx_lint", resource_name):
        print("Don't have file %r to write." % filename)
        return 2

    if os.path.exists(filename):
        print("Checking existing copy of %s" % filename)
        tef = TamperEvidentFile(filename)
        if not tef.validate():
            bak_name = amend_filename(filename, "_backup")
            print("Your copy of %s seems to have been edited, renaming it to %s" % (filename, bak_name))
            if os.path.exists(bak_name):
                print("A previous %s exists, deleting it" % bak_name)
                os.remove(bak_name)
            os.rename(filename, bak_name)

    print("Reading edx_lint/files/%s" % filename)
    cfg = configparser.RawConfigParser()
    resource_string = pkg_resources.resource_string("edx_lint", resource_name).decode("utf8")

    # pkg_resources always reads binary data (in both python2 and python3).
    # ConfigParser.read_string only exists in python3, so we have to wrap the string
    # from pkg_resources in a cStringIO so that we can pass it into ConfigParser.readfp.
    cfg.readfp(cStringIO(resource_string), resource_name)   # pylint: disable=deprecated-method

    if os.path.exists(tweaks_name):
        print("Applying local tweaks from %s" % tweaks_name)
        cfg_tweaks = configparser.RawConfigParser()
        cfg_tweaks.read([tweaks_name])

        merge_configs(cfg, cfg_tweaks)

    print("Writing %s" % filename)
    output_text = cStringIO()
    output_text.write(WARNING_HEADER.format(filename=filename, tweaks_name=tweaks_name))
    cfg.write(output_text)

    out_tef = TamperEvidentFile(filename)
    if six.PY2:
        output_bytes = output_text.getvalue()
    else:
        output_bytes = output_text.getvalue().encode("utf8")
    out_tef.write(output_bytes)

    return 0


def amend_filename(filename, amend):
    """Amend a filename with a suffix.

    amend_filename("foo.txt", "_tweak") --> "foo_tweak.txt"

    """
    base, ext = os.path.splitext(filename)
    amended_name = base + amend + ext
    return amended_name
