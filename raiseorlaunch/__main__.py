#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is the CLI for raiseorlaunch. A run-or-raise-application-launcher
 for i3 window manager.
"""

import os
import argparse
from distutils import spawn
from raiseorlaunch import (Raiseorlaunch, RaiseorlaunchWorkspace,
                           __title__, __version__, __description__)


def verify_app(parser, application):
    """
    Verify the given application argument.
    """
    def error_handle():
        """
        Handle a verify_app error.
        """
        parser.error('{} is not an executable!'.format(application))

    is_exe = spawn.find_executable(application)
    if not is_exe:
        error_handle()
    elif is_exe == application:
        if not os.access(application, os.X_OK):
            error_handle()
    return application


def set_command(parser, args):
    """
    Set args.command, if --exec is omitted.
    In this order:
    class, instance, title.
    """
    if not args.command:
        if args.wm_class:
            args.command = args.wm_class.lower()
        elif args.wm_instance:
            args.command = args.wm_instance.lower()
        elif args.wm_title:
            args.command = args.wm_titlef.lower()

    if not args.command:
        parser.error('No executable provided!')

    args.command = args.command

    verify_app(parser, args.command.split(' ')[0])

    return args


def check_args(parser, args):
    """
    Verify that at least one argument is given.
    """
    if args.scratch and args.workspace:
        parser.error("You cannot use the scratchpad on a specific workspace.")


def parse_arguments():
    """
    Parse all arguments.
    """
    parser = argparse.ArgumentParser(prog=__title__,
                                     description=__description__,
                                     formatter_class=argparse.
                                     RawDescriptionHelpFormatter)

    parser.add_argument("-i", "--ignore-case", dest="ignore_case",
                        action="store_true", help="ignore case.")

    parser.add_argument("-w", "--workspace", dest="workspace",
                        help="workspace to use.")
    parser.set_defaults(workspace=None)

    parser.add_argument("-r", "--scratch", dest="scratch",
                        action="store_true", help="use scratchpad")

    parser.add_argument("-e", "--exec", dest="command",
                        help="command to execute. If omitted, -c, -s or "
                        "-t will be used (lower-case). "
                        "Careful: The command will not be checked "
                        "prior to execution!")
    parser.set_defaults(command=None)

    parser.add_argument("-c", "--class", dest="wm_class",
                              help="the window class.")
    parser.set_defaults(wm_class='')

    parser.add_argument("-s", "--instance", dest="wm_instance",
                        help="the window instance.")
    parser.set_defaults(wm_instance='')

    parser.add_argument("-t", "--title", dest="wm_title",
                        help="the window title.")
    parser.set_defaults(wm_title='')

    parser.add_argument('--version', action='version',
                        version=__version__)

    args = parser.parse_args()

    check_args(parser, args)

    args = set_command(parser, args)

    return args, parser


def main():
    args, parser = parse_arguments()

    try:
        if not args.workspace:
            rol = Raiseorlaunch(command=args.command,
                                wm_class=args.wm_class,
                                wm_instance=args.wm_instance,
                                wm_title=args.wm_title,
                                ignore_case=args.ignore_case,
                                scratch=args.scratch)
        else:
            rol = RaiseorlaunchWorkspace(command=args.command,
                                         wm_class=args.wm_class,
                                         wm_instance=args.wm_instance,
                                         wm_title=args.wm_title,
                                         ignore_case=args.ignore_case,
                                         workspace=args.workspace)
    except TypeError as e:
        if str(e) == ('You need to specify '
                      '"wm_class", "wm_instance" or "wm_title.'):
            parser.error('You need to specify at least one argument out '
                         'of -c, -s or -t.')
        else:
            raise

    rol.run()


if __name__ == "__main__":
    main()
