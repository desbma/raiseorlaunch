"""
This is the module for raiseorlaunch. A run-or-raise-application-launcher
 for i3 window manager.
"""


from __future__ import print_function


__title__ = 'raiseorlaunch'
__description__ = 'Run-or-raise-application-launcher for i3 window manager.'
__version__ = '0.1.2'
__license__ = 'MIT'
__author__ = 'Fabio Rämi'


import sys
from subprocess import Popen
from time import sleep
try:
    import i3
except ImportError:
    print("\033[31;1mError: Module i3 not found.\033[0m", file=sys.stderr)
    sys.exit(1)


class RolBase(object):
    """

    Base class for raiseorlaunch.

    Args:
        command (str): The command to execute, if no matching window was found.
        wm_class (str, optional): The window class to look for.
        wm_instance (str, optional): The window instance to look for.
        wm_title (str, optional): The window title to look for.
        ignore_case (bool, optional): Ignore case when comparing
                                      window-properties with provided
                                      arguments.

    """

    def __init__(self,
                 command,
                 wm_class='',
                 wm_instance='',
                 wm_title='',
                 ignore_case=False):
        self.command = command
        self.wm_class = wm_class
        self.wm_instance = wm_instance
        self.wm_title = wm_title
        self.ignore_case = ignore_case
        self.windows = []
        self._check_args()

    def run(self):
        """
        Search for running window that matches provided properties
        and act accordingly.
        """
        raise NotImplementedError

    def _check_args(self):
        """
        Verify that window properties are provided.
        """
        if not self.wm_class and not self.wm_instance and not self.wm_title:
            raise TypeError('You need to specify '
                            '"wm_class", "wm_instance" or "wm_title.')

    def _run_command(self):
        """
        Run the specified command.
        """
        Popen(self.command, shell=True)

    def _get_current_ws(self):
        """
        Get the current workspace name.
        """
        for ws in i3.get_workspaces():
            if ws['focused']:
                return ws['name']

    def _compile_props_dict(self, win, scratch):
        if scratch == 'none':
            scratch = False
        else:
            scratch = True
        result = {'id': win['window'],
                  'wm_class': win['window_properties']['class'],
                  'wm_instance': win['window_properties']['instance'],
                  'wm_title': win['window_properties']['title'],
                  'focused': win['focused'],
                  'scratch': scratch}
        if self.ignore_case:
            for i in ['wm_class', 'wm_instance', 'wm_title']:
                result[i] = result[i].lower()
        return result

    def _get_window_properties(self, tree):
        for item in tree:
            if item['window']:
                props = self._compile_props_dict(item,
                                                 item['scratchpad_state'])
                self.windows.append(props)
            if 'nodes' in item:
                self._get_window_properties(item['nodes'])
            if 'floating_nodes' in item:
                self._get_window_properties(item['floating_nodes'])

    def _get_window_tree(self):
        """
        Get the current window tree.
        """
        return i3.filter()

    def _compare_running(self, window):
        """
        Compare the properties of a running window with the ones provided.
        """
        c_wm_class = (self.wm_class.lower() if self.ignore_case
                      else self.wm_class)
        c_wm_instance = (self.wm_instance.lower() if self.ignore_case
                         else self.wm_instance)
        c_wm_title = (self.wm_title.lower() if self.ignore_case
                      else self.wm_title)

        if c_wm_class:
            if not c_wm_class == window['wm_class']:
                return False
        if c_wm_instance:
            if not c_wm_instance == window['wm_instance']:
                return False
        if c_wm_title:
            if not c_wm_title == window['wm_title']:
                return False
        return True

    def _get_properties_of_running_app(self):
        """
        Check if application is running on the (maybe) given workspace.
        """
        tree = self._get_window_tree()
        self._get_window_properties(tree)
        running = {'id': None, 'scratch': None, 'focused': None}
        if not self.windows:
            return running

        # Iterate over the windows
        for window in self.windows:

            if not self._compare_running(window):
                continue

            running['scratch'] = window['scratch']
            running['id'] = window['id']
            running['focused'] = window['focused']

        return running


class Raiseorlaunch(RolBase):
    """

    Run or raise an application in i3 window manager.

    Additional args:
        scratch (bool, optional): Indicate if the scratchpad should be used.

    """

    def __init__(self, *args, **kwargs):
        if 'scratch' in kwargs:
            self.scratch = kwargs['scratch']
            kwargs.pop('scratch')
        else:
            self.scratch = False
        super(Raiseorlaunch, self).__init__(*args, **kwargs)

    def run(self):
        """
        Search for running window that matches provided properties
        and act accordingly.
        """
        running = self._get_properties_of_running_app()
        if running['id']:
            if self.scratch:
                i3.command('[id={}]'.format(running['id']),
                           'scratchpad',
                           'show')
            else:
                current_ws_old = self._get_current_ws()
                if not running['focused']:
                    i3.focus(id=running['id'])
                else:
                    if current_ws_old == self._get_current_ws():
                        if not running['scratch_id']:
                            i3.command('workspace', current_ws_old)
        else:
            self._run_command()
            if self.scratch:
                sleep(1.5)
                running = self._get_properties_of_running_app()
                i3.command('[id={}]'.format(running['id']), 'move',
                           'scratchpad')
                i3.command('[id={}]'.format(running['id']), 'scratchpad',
                           'show')


class RaiseorlaunchWorkspace(RolBase):
    """

    Run or raise an application on a specific workspace in i3 window manager.

    Additional args:
        workspace (str): The workspace that should be used for the application.

    """

    def __init__(self, *args, **kwargs):
        if 'workspace' in kwargs:
            self.workspace = kwargs['workspace']
            kwargs.pop('workspace')
        else:
            raise TypeError("__init__() missing 1 required positional "
                            "argument: 'workspace'")
        super(RaiseorlaunchWorkspace, self).__init__(*args, **kwargs)

    def run(self):
        """
        Search for running window that matches provided properties
        and act accordingly.
        """
        running = self._get_properties_of_running_app()
        if running['id']:
            current_ws_old = self._get_current_ws()

            if not running['focused']:
                i3.focus(id=running['id'])
            else:
                if current_ws_old == self.workspace:
                    i3.command('workspace', self.workspace)
        else:
            if not self._get_current_ws() == self.workspace:
                i3.command('workspace', self.workspace)
            self._run_command()

    def _get_window_tree(self):
        """
        Get the current window tree on the provided workspace.
        """
        return i3.filter(name=self.workspace)
