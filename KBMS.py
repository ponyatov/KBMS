# -*- coding: utf-8 -*-

import os,sys

## ######################################### Marvin Minsky extended frame model

class Frame:
    
    def __init__(self,V):
        self.type = self.__class__.__name__.lower()
        if isinstance(V, Vector):
            self.val  = V.val
            self.nest = V.nest
        else:
            self.val  = V
            self.nest = []
        self.slot = {}
        self.immed = False
        
    def __repr__(self):
        return self.dump()
    def dump(self,depth=0,prefix='',voc=True):
        tree = self._pad(depth) + self.head(prefix)
        if not depth: Frame._dumped = []
        if self in Frame._dumped: return tree + ' _/'
        else: Frame._dumped.append(self)
        if voc:
            for i in self.slot:
                tree += self.slot[i].dump(depth+1,prefix=i+' = ')
        for j in self.nest:
            tree += j.dump(depth+1)
        return tree
    def head(self,prefix=''):
        return '%s<%s:%s> @%x' % (prefix,self.type,self._val(),id(self))
    def _pad(self,depth):
        return '\n' + ' '*4 * depth
    def _val(self):
        return str(self.val)
    
    def __getitem__(self,key):
        return self.slot[key]
    def __setitem__(self,key,that):
        self.slot[key] = that ; return self
    def __lshift__(self,that):
        self.slot[that.val] = that ; return self
    def __floordiv__(self,that):
        return self.push(that)
    
    def push(self,that):
        self.nest.append(that) ; return self
    def pop(self):
        return self.nest.pop()
    def pip(self):
        return self.nest.pop(-2)
    def top(self):
        return self.nest[-1]
    def tip(self):
        return self.nest[-2]
    def dropall(self):
        self.nest = [] ; return self
    def dup(self):
        self // self.top()
    def drop(self):
        self.pop()
    def swap(self):
        self // self.pip()
    def over(self):
        self // self.tip()
    
    def eval(self,vm):
        vm // self
        
## ##################################################### primitive/scalar types

class Primitive(Frame): pass

class Symbol(Primitive): pass

class String(Primitive): pass

class Number(Primitive):
    def __init__(self,V):
        Primitive.__init__(self,float(V))

class Integer(Number):
    def __init__(self,V):
        Primitive.__init__(self,int(V))

class Hex(Integer):
    def __init__(self,V):
        Primitive.__init__(self,int(V[2:],0x10))
    def _val(self):
        return hex(self.val)

class Bin(Integer):
    def __init__(self,V):
        Primitive.__init__(self,int(V[2:],0x02))
    def _val(self):
        return bin(self.val)

## ############################################################ data containers

class Container(Frame): pass

class Vector(Container): pass

class Stack(Container): pass

class Dict(Container): pass

class Queue(Container): pass

## #################################### active (executable/evaluatable) objects

class Active(Frame): pass

class VM(Active):
    def __init__(self,V):
        Active.__init__(self, V)
        self.compile = []
    def __setitem__(self,key,F):
        if callable(F): self[key] = Cmd(F) ; return self
        else: return Active.__setitem__(self,key,F)
    def __lshift__(self,F):
        if callable(F): return self << Cmd(F)
        else: return Active.__lshift__(self, F)

class Cmd(Active):
    def __init__(self,F,I=False):
        Active.__init__(self, F.__name__)
        self.immed = I
        self.fn = F
    def eval(self,vm):
        self.fn(vm)
        
class Seq(Active,Vector): pass

## ######################################################################## I/O

class IO(Frame): pass

class Dir(IO): pass

class File(IO): pass

## #################################################################### network

class Net(IO): pass

class Ip(Net): pass

class Port(Net): pass

class Url(Net): pass

class Email(Net): pass

## ###################################################### web interface /flask/

class Web(Net):
    def __init__(self,V):
        Net.__init__(self, V)
        
        flask     = ( self << pyModule('flask'    ))['flask'    ].module
        flask_wtf = ( self << pyModule('flask_wtf'))['flask_wtf'].module
        wtforms   = ( self << pyModule('wtforms'  ))['wtforms'  ].module
        
        class CLI(flask_wtf.FlaskForm):
            pad = wtforms.TextAreaField('pad',
                                        render_kw={'rows':5,'autofocus':'true'},)
            go  = wtforms.SubmitField  ('go' )
        
        app = flask.Flask(V) ; app.config['SECRET_KEY'] = os.urandom(32)
        
        self['route'] = Vector('route')
        
        self << File('CSS')
        self['CSS']['background']    = Color('black')
        self['CSS']['color']         = Color('lightgreen')
        self['CSS']['font']          = Font('monospace')
        self['CSS']['font']['size']  = String('3mm')
        @app.route('/css.css')
        def css():
            return flask.Response(
                flask.render_template('css.css',vm=vm,web=self),
                mimetype='text/css')
        self['route'] << Fn(css)

        @app.route('/favicon.ico')
        @app.route('/logo.png')
        def favicon():
            self['ico'] = File('logo.png')
            return app.send_static_file('logo.png')
        self['route'] << Fn(favicon)
        
        self['js'] = Vector('libs')
        @app.route('/<lib>.js')
        def js(lib):
            self['js'] << jsLib(lib) // File(lib+'.js')
            return app.send_static_file(lib+'.js')
        self['route'] << Fn(js)
            
        @app.route('/',methods=['GET','POST'])
        def index():
            form = CLI()
            if form.validate_on_submit():
                vm // String(form.pad.data) ; INTERPRET(vm)
            return flask.render_template('index.html',vm=vm,frame=vm,web=self,form=form)
        self['route'] << Fn(index)
        
        @app.route('/<path:path>',methods=['GET','POST'])
        def path(path):
            form = CLI()
            if form.validate_on_submit():
                vm // String(form.pad.data) ; INTERPRET(vm)
            return flask.render_template('index.html',vm=vm,frame=vm[path],web=self,form=form)
        self['route'] << Fn(path)
        
        self['IP'] = Ip('127.0.0.1')
        self['PORT'] = Port(8888)
        app.run(host=self['IP'].val,port=self['PORT'].val,
                debug=True,extra_files='KBMS.ini')
        
## #################################################################### gamedev

class Game(Frame):
    def __init__(self,V):
        Frame.__init__(self, V)
        vm['GAME'] = self
        self << pyModule('pygame') ; pygame = self['pygame'].module
        W = 640 ; H = 480
        
        self['display'] = Display('',W,H)
        self['screen'] = Surface('green box',W/11,H/11,fill=vm['COLOR']['BLUE'])
        self['display'] // self['screen']
        QQ(self)
        
    def eval(self,vm):
        self['display'].eval(self)
        QQ(self)

        while True:
            window.blit(screen,(0,0))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    QQ(vm)
                    
class Display(Game):
    def __init__(self,V,W=640,H=480):
        Frame.__init__(self,V)
        self['W'] = Integer(W)
        self['H'] = Integer(H)
    def eval(self,game):
        pygame = game['pygame'].module
        W,H = self['W'].val,self['H'].val
        window = pygame.display.set_mode((W,H))
        pygame.display.set_caption(vm.head())
        
class Surface(Display):
    def __init__(self,V,W,H,fill):
        Display.__init__(self,V,W,H)
        self['fill'] = fill

## ################################################################ documenting

class Doc(Frame): pass

class Font(Doc): pass

class Color(Doc):
    def __init__(self,V,RGB=(0,0,0)):
        Doc.__init__(self, V)
        self.rgb = RGB
        
class Title(Doc): pass
class Author(Doc): pass

## ############################################################ metaprogramming

class Meta(Frame): pass

class Module(Meta): pass

class Fn(Meta):
    def __init__(self,F):
        Meta.__init__(self, F.__name__)

## ################################################ code integration/generation

class Lang(Meta): pass

## ######################################################################### JS

class JS(Lang): pass
class jsLib(JS,File): pass
class jsFn(JS,Fn): pass

## ####################################################################### Java

class Java(Lang): pass

## ######################################################################### C#

class Charp(Lang): pass

## ############################################################# embedded C/C++

class emC(Lang): pass
class Cpp(emC): pass

## ###################################################################### FORTH

class FORTH(Lang): pass
class metaL(FORTH): pass 

## ##################################################################### Python 

class Python(Lang): pass

class pyModule(Python,Module):
    def __init__(self,M):
        Python.__init__(self, M)
        self.module = __import__(M)

## ##################################################### global virtual machine

vm = VM('metaL') ; vm['VM'] = vm

## ###################################################################### debug

def BYE(vm): sys.exit(0)
vm << BYE

def Q(vm): print(vm.dump(voc=False))
vm['?'] = Cmd(Q,I=True)

def QQ(vm): print(vm.dump(voc=True)) ; BYE(vm)
vm['??'] = Cmd(QQ,I=True)

## ########################################################### stack operations

def DOT(vm): vm.dropall()
vm['.'] = DOT

def DUP(vm): vm.dup()
vm << DUP

def DROP(vm): vm.drop()
vm << DROP

def SWAP(vm): vm.swap()
vm << SWAP

def OVER(vm): vm.over()
vm << OVER

## ######################################################## frame manipulations

def EQ(vm): addr = vm.pop() ; vm[addr.val] = vm.pop()
vm['='] = EQ

def LSHIFT(vm): vm // ( vm.pip() << vm.pop() )
vm['<<'] = LSHIFT

def PUSH(vm): what = vm.pip() ; vm.top() // what
vm['//'] = PUSH

def ATTR(vm): where = vm.pop() ; what = vm.pop() ; vm.top()[where.val] = what
vm['/<'] = ATTR

def rFETCH(vm): where = vm.pop() ; vm // vm.pop()[where.val]
vm['/@'] = rFETCH

def STOR(vm):
    where = vm.pop() ; addr = vm.pop() ; what = vm.pop()
    where[addr.val] = what
    vm // where
vm['/='] = STOR

## ############################################################ metaprogramming

def MODULE(vm): vm // Module(vm.pop().val)
vm << MODULE

## ############################################ PLY-powered parser (lexer only)
    
import ply.lex as lex

tokens = ['symbol','string','number','integer','hex','bin']

t_ignore = ' \t\r\n'
t_ignore_comment = r'[#\\].*'

states = (('str','exclusive'),('comment','exclusive'),)

t_str_ignore = ''
def t_str(t):
    r'\''
    t.lexer.push_state('str') ; t.lexer.string = ''
def t_str_str(t):
    r'\''
    t.lexer.pop_state() ; return String(t.lexer.string)
def t_str_char(t):
    r'.'
    t.lexer.string += t.value
    
t_comment_ignore = ''
def t_comment(t):
    r'\('
    t.lexer.push_state('comment')
def t_comment_comment(t):
    r'\)'
    t.lexer.pop_state()
def t_comment_any(t):
    r'.'
    pass

def t_hex(t):
    r'0x[0-9a-fA-F]+'
    return Hex(t.value)
def t_bin(t):
    r'0b[01]+'
    return Bin(t.value)

def t_number_exp(t):
    r'[+\-]?[0-9]+[eE][+\-]?[0-9]+'
    return Number(t.value)
def t_number_dot(t):
    r'[+\-]?[0-9]*\.[0-9]+'
    return Number(t.value)
    
def t_integer(t):
    r'[+\-]?[0-9]+'
    return Integer(t.value)

def t_symbol(t):
    r'[`]|[^ \t\r\n\#\\]+'
    return Symbol(t.value)

def t_ANY_error(t): raise SyntaxError(t)

lexer = lex.lex()

## ################################################################ interpreter

def QUOTE(vm): WORD(vm)
vm['`'] = QUOTE

def WORD(vm):
    token = lexer.token()
    if token: vm // token ; return True
    return False

def FIND(vm):
    token = vm.pop()
    try: vm // vm[token.val] ; return True
    except KeyError: vm // vm[token.val.upper()] ; return True
    return False

def EVAL(vm):
    vm.pop().eval(vm)
    
def INTERPRET(vm):
    lexer.input(vm.pop().val)
    while True:
        if not WORD(vm): break;
        if isinstance(vm.top(),Symbol):
            if not FIND(vm): raise SyntaxError(vm)
        if not vm.compile or vm.top().immed:
            EVAL(vm)
        else:
            COMPILE(vm)
            
## ################################################################### compiler

def COMPILE(vm): vm.compile[-1] // vm.pop()

def REC(vm): vm.compile[-1] // vm.compile[-1]
vm['REC'] = Cmd(REC,I=True)
        
def LQ(vm): vm.compile.append(Vector(''))
vm['['] = Cmd(LQ,I=True)

def RQ(vm):
    item = vm.compile.pop()
    if vm.compile: vm.compile[-1] // item
    else: vm // item
vm[']'] = Cmd(RQ,I=True)

def LC(vm): vm.compile.append(Seq(''))
vm['{'] = Cmd(LC,I=True)

def RC(vm): RQ(vm)
vm['}'] = Cmd(RC,I=True)

## ######################################################################## i/o

def DIR(vm): vm // Dir(vm.pop().val)
vm << DIR

def FILE(vm): vm // File(vm.pop().val)
vm << FILE

## #################################################################### network

def URL(vm): vm // Url(vm.pop().val)
vm['URL'] = URL

def EMAIL(vm): vm // Email(vm.pop().val)
vm['EMAIL'] = EMAIL

def WEB(vm): vm['WEB'] = Web(vm.val)
vm << WEB

## ###################################################################### FORTH

vm['FORTH'] = Lang('FORTH')
vm['metaL'] = Lang('metaL')

## ################################################################ documenting

vm << Vector('COLOR')
vm['COLOR']['RED'   ] = Color('red'   ,(0xFF,0x00,0x00))
vm['COLOR']['GREEN' ] = Color('green' ,(0x00,0xFF,0x00))
vm['COLOR']['BLUE'  ] = Color('blue'  ,(0x00,0x00,0xFF))
vm['COLOR']['CYAN'  ] = Color('cyan'  ,(0x00,0xFF,0xFF))
vm['COLOR']['YELLOW'] = Color('yellow',(0xFF,0xFF,0x00))

def dotTITLE(vm): vm // Title(vm.pop().val)
vm['.title'] = dotTITLE

def dotAUTHOR(vm): vm // Author(vm.pop().val)
vm['.author'] = dotAUTHOR

## #################################################################### gamedev

def GAME(vm): vm['GAME'] = Game(vm.val) ; vm['GAME'].eval(vm)
vm << GAME

def DISPLAY(vm): vm // Display(vm.pop().val)
vm << DISPLAY

def SURFACE(vm): vm // Surface(vm.pop().val,320,240,fill=vm['COLOR']['BLUE'])
vm << SURFACE

## ################################################################ system init

if __name__ == '__main__':
    for infile in sys.argv[1:]:
        vm // String(open(infile).read())
        INTERPRET(vm)
    QQ(vm)
