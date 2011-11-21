
# Create a base class to subclass from (instead of subclassing cmd.Cmd)

import cmd
import os


from cloudshell.utils import color

class base_shell(cmd.Cmd, object):
    def do_EOF(self, string):
        # make sure that the new prompt (either internal or returned to shell)
        # is on its own line.
        print
        return True

    do_exit = do_EOF

    def set_prompt(self, username, breadcrumbs):
        c_pri = color.set('blue')
        c_un = color.set('cyan')
        self.prompt = (c_pri + 'CloudShell ' + c_un + username + 
                       c_pri + ' ' + ' > '.join(breadcrumbs) + 
                       color.clear() + ' $ ')

    def do_shell(self, string):
        """Run a shell command"""
        os.system(string)

    def do_python(self, string):
        """Run a python command

        This does not do ANY checking for syntax, 
        nor does it do any exception handling.
        """
        if len(string):
            pass

