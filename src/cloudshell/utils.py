
import shlex

class color:
    """ANSI Color wrapper"""

    prefix = "\033["
    postfix = "m"
    color_codes = {
            'black':30,
            'red':31,
            'green':32,
            'yellow':33,
            'blue':34,
            'purple':35,
            'cyan':36,
            'grey':37
    }
    background = 10
    bold = 1

    @classmethod
    def clear(self):
        """Return the no-color ANSI color."""
        return self.prefix + '00' + self.postfix

    @classmethod
    def set(self,color,bold=False,bg=False):
        """
        Provide an ANSI Color control code.

        color is the only required field and must be in the list of colors
        defined in the color_codes dictionary attribute to this class.

        bold and bg are by-default False boolean values that will tweak 
        the color code returned.  bold will change the first number from
        00 to 01 while bg adds 10 to the color code in the second.

        returns \\033[**;??;##m  where ** is either 00 or 01 (bold)
                                and ?? is the color_code requested
                                and ## is the background if set

        """
        if color == 'white':
            color = 'grey'
            bold = True
        second = self.color_codes[color]
        if bold:
            first = '01'
        else:
            first = '00'
        output = self.prefix + first + ';' + str(second)
        if bg:
            output += ';' + str(self.color_codes[bg] + self.background)
        return output + self.postfix
