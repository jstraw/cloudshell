
# Create a base class to subclass from (instead of subclassing cmd.Cmd)

import cmd
import os
import readline


from cloudshell.utils import color

class base_shell(cmd.Cmd, object):

    _history_file_base = os.path.expanduser("~/.cloudshell/history")

    def do_history(self, string):
        for i in range(1, min(20, readline.get_current_history_length())):
            print(readline.get_history_item(i))

    do_hist = do_history

    def do_EOF(self, string):
        # make sure that the new prompt (either internal or returned to shell)
        # is on its own line.
        print '\n'
        return True

    do_exit = do_EOF

    def error(self, text, *args):
        c_error = color.set('purple', bold=True)
        text += ' ' + ' '.join(args)
        print c_error, "Error:", text, color.clear()

    def alert(self, text, *args):
        c_alert = color.set('red')
        text += ' ' + ' '.join(args)
        print c_alert, text, color.clear()

    def warning(self, text, *args):
        c_warn = color.set('yellow', bold=True)
        text += ' ' + ' '.join(args)
        print c_warn, text, color.clear()

    def notice(self, text, *args):
        c_notice = color.set('green')
        text += ' ' + ' '.join(args)
        print c_notice, text, color.clear()

    def set_prompt(self, username, breadcrumbs):
        c_pri = color.set('green')
        c_un = color.set('cyan')
        c_d = color.set('green')
        self.prompt = c_pri + 'CS ' + c_un + username + \
                       c_pri + ' ' + ' > '.join(breadcrumbs) + \
                       c_d + '$ ' + color.clear()

    def do_shell(self, string):
        """Run a shell command"""
        os.system(string)

    def do_python(self, string):
        """Run a python debug shell"""
        self.notice("Press c to return to cloudshell")
        import pdb; pdb.set_trace()

