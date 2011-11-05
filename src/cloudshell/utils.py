
class color:
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

    def clear(self):
        return self.prefix + '00' + self.postfix

    def set(self,color,bold=False,bg=False):
        if color == 'white':
            color = 'grey'
            bold = True
        color_code = self.color_codes[color]
        if bg:
            color_code += self.background
        if bold:
            return self.prefix + '01;' + str(color_code) + self.postfix
        else:
            return self.prefix + '00;' + str(color_code) + self.postfix
